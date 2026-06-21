import numpy as np
import xarray as xr

import dask.array as da
import torch
import random
import time


from omnicloudmask import predict_from_array
from scipy.ndimage import maximum_filter, binary_dilation



# TODO: explore this more in detail !
# ------------------ Determinism setup ------------------ #
def setup_torch_determinism(seed=0):
    """   
    Make Torch, NumPy and Python RNGs as deterministic as possible
    and avoid cuDNN picking non-deterministic kernels.
    Call this ONCE at program start, before any model inference.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    try:
        torch.use_deterministic_algorithms(True)
    except Exception as e:
        print(
            "Warning: torch.use_deterministic_algorithms(True) failed; "
            "some ops may remain non-deterministic:\n", e
        )



def generate_cloud_mask(
    ds: xr.Dataset,
    chunk_time=None,
    target_mb=50,
):
    """
    Generate and attach a deterministic cloud mask using OmniCloudMask inference.

    This high-level wrapper optionally derives an appropriate temporal chunk size
    based on a target memory footprint and then calls `add_cloud_mask()`.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset containing at least the spectral bands B04, B03, and B08.
        Expected dimensions are (time, y, x).
    chunk_time : int or None, optional
        Number of timesteps processed per inference batch. If provided, this value
        is passed directly to `add_cloud_mask`. If None, the value is automatically
        derived from `target_mb`.
    target_mb : int or None, optional
        Approximate memory target (MiB) used to estimate the temporal chunk size
        when `chunk_time` is None. Default is 50.

    Returns
    -------
    tuple[xr.Dataset, xr.DataArray]
        ds_out : xr.Dataset
            Dataset with an added variable `cloud_mask` of shape (time, y, x).
        cloud_mask : xr.DataArray
            Fully computed cloud mask.

    Notes
    -----
    - Deterministic behaviour is enforced via `setup_torch_determinism()`.
    - Cloud mask classes:
        0 = Clear
        1 = Thick Cloud
        2 = Thin Cloud
        3 = Cloud Shadow
    """

    setup_torch_determinism(seed=0)

    cmask_decode = {
        0: "Clear (Cloud Free)",
        1: "Thick Cloud",
        2: "Thin Cloud",
        3: "Cloud Shadow",
    }

    # --- helper: auto-derive chunk_time from target_mb (MiB) ---
    def _auto_chunk_time_from_target_mb(
        ds_ref,
        chunk_time=None,
        target_mb=50,
        band_vars=("B04", "B03", "B08"),
        dtype=np.float32,
    ):
        """
        estimate time chunk size based on target memory
    
        determines how many time steps should be included in one chunk
        so that a block with shape (time_chunk, n_bands, y, x) is close
        to the specified target_mb size.
    
        ds_ref: xarray.Dataset
            reference xarray Dataset
    
        chunk_time: int or None
            predefined time chunk size
    
        target_mb: int
            target chunk size in MiB
    
        band_vars: tuple
            variables used to estimate memory footprint
    
        dtype: numpy dtype
            data type assumed for memory calculation
    
        returns
        -------
        chunk_time: int or None
            suggested time chunk size
            None if no time dimension exists
        """
        band0 = ds_ref[band_vars[0]]
        if "time" not in band0.dims:
            return None  # nothing to chunk over

        # assume dims like (time, y, x) or (time, x, y)
        time_dim = "time"
        # infer spatial dims by excluding time
        spatial_dims = tuple(d for d in band0.dims if d != time_dim)
        if len(spatial_dims) != 2:
            raise ValueError(f"Expected 2 spatial dims, got {spatial_dims}")

        s0, s1 = spatial_dims
        nt = band0.sizes[time_dim]
        ny = band0.sizes[s0]
        nx = band0.sizes[s1]

        n_bands = len(band_vars)
        bytes_per_val = np.dtype(dtype).itemsize
        # bytes per single time step over all bands and full frame
        bytes_per_timestep = n_bands * ny * nx * bytes_per_val

        if bytes_per_timestep == 0:
            return 1

        target_bytes = target_mb * 1024**2  # MiB → bytes
        steps = max(1, int(target_bytes // bytes_per_timestep))

        # don't exceed available time length
        return min(steps, int(nt))

    
    # --- choose chunk_time ---
    if chunk_time is None:
        if target_mb is not None:
            auto_ct = _auto_chunk_time_from_target_mb(
                ds,
                band_vars=("B04", "B03", "B08"),
                target_mb=target_mb,
                dtype=np.float32,
            )
            if auto_ct is not None and auto_ct > 0:
                chunk_time = auto_ct
                print(
                    f"[generate_cloud_mask] auto chunk_time from "
                    f"target_mb={target_mb} MiB → {chunk_time}"
                )
            else:
                # fallback if no time dim or weird sizes
                chunk_time = 10
                print(
                    f"[generate_cloud_mask] no valid time dim; "
                    f"falling back to chunk_time={chunk_time}"
                )
        else:
            # no target_mb given, use default
            chunk_time = 10
            print(
                f"[generate_cloud_mask] target_mb=None; "
                f"falling back to chunk_time={chunk_time}"
            )

    # --- main call into  ---
    ds_with_mask, cloud_mask = add_cloud_mask(
        ds,
        band_vars=("B04", "B03", "B08"),
        time_dim="time",
        y_dim="y",
        x_dim="x",
        band_dim="band",
        time_chunk=int(chunk_time),
    )

    
    # Compute ONCE to freeze the model output (no recompute on later .compute())
    cloud_mask = cloud_mask.compute()
    ds_with_mask = ds_with_mask.assign(cloud_mask=cloud_mask)

    # Attach decode mapping as attribute
    ds_with_mask["cloud_mask"].attrs["decode"] = cmask_decode

    return ds_with_mask, cloud_mask


def add_cloud_mask(
    ds,
    band_vars=("B04", "B03", "B08"),
    time_dim="time",
    y_dim="y",
    x_dim="x",
    band_dim="band",
    time_chunk=10,
):
    """
    Generate and attach a reproducible cloud mask with dimensions (time, y, x)
    using OmniCloudMask inference.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset containing the required spectral bands.
    band_vars : tuple of str, optional
        Names of band variables used as (R, G, NIR) input to the model.
        Default is ("B04", "B03", "B08").
    time_dim : str, optional
        Name of the temporal dimension. Default is "time".
    y_dim : str, optional
        Name of the y/spatial row dimension. Default is "y".
    x_dim : str, optional
        Name of the x/spatial column dimension. Default is "x".
    band_dim : str, optional
        Name of the stacked band dimension used internally during inference.
        Default is "band".
    time_chunk : int, optional
        Number of timesteps processed per inference batch. Controls memory usage
        during prediction. Default is 10.

    Returns
    -------
    xr.Dataset
        Dataset with an added variable `cloud_mask` of shape (time, y, x).

    Notes
    -----
    - The function is deterministic when `setup_torch_determinism()` is called
      prior to inference.
    - Cloud mask classes follow OmniCloudMask encoding:
        0 = Clear
        1 = Thick Cloud
        2 = Thin Cloud
        3 = Cloud Shadow
    """

    # Use CPU + deterministic behaviour as much as possible
    predict_kwargs = dict(
        inference_device="cpu",    # IMPORTANT for determinism
        mosaic_device="cpu",
        batch_size=1,              # IMPORTANT: sequential patches
        compile_models=False,
        export_confidence=False,
        softmax_output=True,
        no_data_value=0,
        apply_no_data_mask=True,
        pred_classes=4,
        model_download_source="hugging_face",
        patch_size=401,          # <–– bcs my image has less pixels than default setting
        patch_overlap=200,       # <–– consider to do this last two late dynamic, based on size of teh dataset

        #patch_size = min(800, min(H, W))
        #patch_overlap = patch_size // 2
    )

    # --- Ensure the source bands are float32
    R = ds[band_vars[0]].astype("float32")
    G = ds[band_vars[1]].astype("float32")
    N = ds[band_vars[2]].astype("float32")

    # --- Build a (time, band, y, x) array lazily
    bands = xr.concat([R, G, N], dim=band_dim).assign_coords(
        {band_dim: ["R", "G", "N"]}
    )

    # --- Heuristic scale check (sample sparsely on first time slice)
    scale = np.float32(1.0/10000.0)
    bands = bands * scale

    # --- Clean NaNs/lossy values lazily
    bands = xr.apply_ufunc(
        da.nan_to_num,
        bands,
        kwargs={"nan": 0.0, "posinf": 1.0, "neginf": 0.0},
        dask="parallelized",
        output_dtypes=[np.float32],
    )

    # --- Chunk along time
    bands = bands.chunk(
        {
            time_dim: time_chunk,
            band_dim: 3,
            y_dim: -1,
            x_dim: -1,
        }
    )

    # --- Per-image function: (3, H, W) -> (H, W)
    def _predict_chunk(arr3yx: np.ndarray) -> np.ndarray:
        arr3yx = arr3yx.astype("float32", copy=False)
        pred = predict_from_array(arr3yx, **predict_kwargs)  # (1,H,W) or (H,W)

        # Squeeze leading class dimension if present
        if pred.ndim == 3 and pred.shape[0] == 1:
            pred = pred[0]   # -> (H, W)

        return pred.astype("uint8", copy=False)

    # Todo: rewrite this to make faste rcalulation 
    # --- Apply across time
    cloud_mask = xr.apply_ufunc(
        _predict_chunk,
        bands,
        input_core_dims=[[band_dim, y_dim, x_dim]],  # (3, H, W)
        output_core_dims=[[y_dim, x_dim]],           # (H, W)
        dask="parallelized",
        vectorize=True,
        output_dtypes=[np.uint8],
        keep_attrs=True,
    )

    cloud_mask = cloud_mask.rename("cloud_mask").assign_attrs(
        classes="0=Clear, 1=Thick Cloud, 2=Thin Cloud, 3=Cloud Shadow"
    )

    ds_out = ds.assign(cloud_mask=cloud_mask)
    return ds_out, cloud_mask






def burn_buffered_cloud_mask(
    Hds: xr.Dataset,
    var_of_interest=("sWDRVI",),          # variables to mask-in (keep only clear/kept pixels)
    mask_name="cloud_mask",               # name of the categorical cloud mask in Hds
    keep_values=(0, 3),                   # classes to KEEP (e.g., 0=Clear, 3=Cloud Shadow)
    buffer_pixels=1,                      # buffer radius in pixels
    ydim=None, xdim=None,                 # spatial dim names; if None, inferred via _infer_xy
    add_keep_mask_name="keep_mask",       # name to attach boolean keep-mask into Hds (optional)
    print_summary=True,                   # print timing + stats nicely
    preview_first_n=5,                    # per-slice preview length if 'time' exists
    enforce_no_spatial_chunks=True,       # HARD GUARANTEE: do not allow spatial chunk splits
    rechunk_spatial_if_needed=False,      # if True: auto-fix by rechunking y/x to -1
):
    """
    Build a buffered 'keep' mask from an existing cloud mask, apply it lazily to variables,
    and return updated dataset + mask + stats + timings.

    IMPORTANT ABOUT CHUNKING
    ------------------------
    Buffering (dilation/max-filter) is a spatial neighborhood operation. If the data are
    chunked in space (x/y split), you can get chunk-edge artifacts unless you use overlap-aware
    operations (we DO use map_overlap internally), but you may still want to strictly enforce
    full spatial tiles (no x/y chunk splits) for safety and reproducibility.

    Returns
    -------
    Hds_out : xr.Dataset
        Dataset with selected variables masked (via .where(keep_mask)).
        Also attaches the boolean keep mask as `add_keep_mask_name` (if provided).
    keep_mask : xr.DataArray (bool)
        Boolean mask where True=keep (clear/allowed), False=mask out.
    stats : dict
        Dictionary with dask-backed xarray scalars and arrays:
          - 'total_bad_original'  : 0-D (int64)
          - 'total_bad_buffered'  : 0-D (int64)
          - 'total_extra_masked'  : 0-D (int64)
          - 'per_slice_extra_masked' (optional): 1-D over time
    timings : dict
        {'build_mask_s': float, 'apply_mask_s': float, 'total_s': float}
    """
    # Infer spatial dims if needed
    if ydim is None or xdim is None:
        ydim, xdim = _infer_xy(Hds)

    # --- safety: enforce "no spatial chunk splits" if requested ---
    if rechunk_spatial_if_needed:
        # Auto-fix: full spatial tiles
        Hds = Hds.chunk({ydim: -1, xdim: -1})

    t0 = time.perf_counter()

    # Build keep mask + stats (existing utility)
    keep_mask, stats = buffered_keep_mask_from_cloudmask_with_stats(
        Hds,
        keep_values=keep_values,
        buffer=buffer_pixels,
        ydim=ydim,
        xdim=xdim,
        cloud_mask_name=mask_name,
    )

    t1 = time.perf_counter()

    # Lazily apply to each variable of interest
    Hds_out = Hds.copy()
    for var in var_of_interest:
        if var in Hds_out:
            Hds_out[var] = Hds_out[var].where(keep_mask)
        else:
            raise KeyError(f"Variable '{var}' not found in dataset.")

    # Optionally attach the keep mask for provenance
    if add_keep_mask_name:
        Hds_out = Hds_out.assign({add_keep_mask_name: keep_mask})

    t2 = time.perf_counter()

    timings = {
        "build_mask_s": t1 - t0,
        "apply_mask_s": t2 - t1,
        "total_s": t2 - t0,
    }

    # Pretty print (safe for dask scalars)
    if print_summary:
        def _to_int_scalar(da0):
            # Handles dask/xarray/numpy scalars
            if hasattr(da0, "compute"):
                da0 = da0.compute()
            if hasattr(da0, "item"):
                return int(da0.item())
            return int(da0)

        nvars = len(var_of_interest)

        # Compute tiny scalars together
        bad_orig_c, bad_buff_c, extra_mask_c = da.compute(
            stats.get("total_bad_original"),
            stats.get("total_bad_buffered"),
            stats.get("total_extra_masked"),
        )

        bad_orig   = _to_int_scalar(bad_orig_c)
        bad_buff   = _to_int_scalar(bad_buff_c)
        extra_mask = _to_int_scalar(extra_mask_c)

        print(
            f"mask built in {timings['build_mask_s']:.2f}s | "
            f"applied to {nvars} var(s) in {timings['apply_mask_s']:.2f}s | "
            f"total {timings['total_s']:.2f}s"
        )
        print(
            f"Original bad: {bad_orig:,} | "
            f"Buffered bad: {bad_buff:,} | "
            f"Extra masked by buffer: {extra_mask:,}"
        )

        # Optional per-time preview
        # if "time" in Hds_out.dims and "per_slice_extra_masked" in stats:
        #     try:
        #         preview = stats["per_slice_extra_masked"].isel(time=slice(0, preview_first_n)).compute()
        #         preview = preview.astype("int64")
        #     except Exception as e:
        #         print(f"(preview skipped: {e})")

    return Hds_out, keep_mask, stats, timings



def buffered_keep_mask_from_cloudmask_with_stats(
    ds: xr.Dataset,
    cloud_mask_name="cloud_mask",
    keep_values=(0, 3),
    buffer=1,
    ydim="y",
    xdim="x",
    engine="maxfilter",   # "maxfilter" or "dilation"
    boundary="nearest",   # scipy modes: "nearest","reflect","mirror","constant","wrap"
    compute_totals=False,
):
    """Build boolean keep-mask by buffering 'bad' pixels in y/x only."""

    if cloud_mask_name not in ds:
        raise KeyError(f"'{cloud_mask_name}' not found in dataset.")

    cm = ds[cloud_mask_name]


    # good = pixels with allowed class; NaNs become False in isin() -> treated as bad
    good = cm.isin(list(keep_values))

    # bad must be strictly boolean and NaN-free BEFORE casting to uint8
    bad = (~good).fillna(False).astype(bool)

    # no buffering case
    if buffer <= 0:
        bad_dilated = bad
    else:
        # ensure dask-backed for map_overlap
        if not isinstance(bad.data, da.Array):
            # keep existing chunking if present; if none, make a single chunk
            # (do NOT introduce spatial splits here)
            bad = bad.chunk({})  # xarray chooses a single chunk when data are numpy-backed

        data = bad.data.astype(np.uint8)

        # axes indices of y/x
        try:
            y_axis = bad.get_axis_num(ydim)
            x_axis = bad.get_axis_num(xdim)
        except ValueError as e:
            raise ValueError(
                f"Could not find spatial dims ('{ydim}','{xdim}') in {bad.dims}"
            ) from e

        depth = {i: 0 for i in range(data.ndim)}
        depth[y_axis] = int(buffer)
        depth[x_axis] = int(buffer)

        if engine == "maxfilter":
            k = int(2 * buffer + 1)
            size = [1] * data.ndim
            size[y_axis] = k
            size[x_axis] = k
            size = tuple(size)

            def _f(block):
                return maximum_filter(block, size=size, mode=boundary)

        elif engine == "dilation":
            # NOTE: the original structure was effectively a 1-element "cross" at [0,0,...]
            # which is not a real 3x3 neighborhood. Here we build a full 3x3 in (y,x).
            struct_shape = [1] * data.ndim
            struct_shape[y_axis] = 3
            struct_shape[x_axis] = 3
            structure = np.ones(struct_shape, dtype=bool)

            def _f(block):
                b = block.astype(bool, copy=False)
                out = binary_dilation(
                    b, structure=structure, iterations=int(buffer), border_value=False
                )
                return out.astype(np.uint8, copy=False)

        else:
            raise ValueError("engine must be 'maxfilter' or 'dilation'")

        dilated_u8 = da.map_overlap(
            _f,
            data,
            depth=depth,
            boundary=boundary,
            trim=True,
            dtype=np.uint8,
        )

        bad_dilated = xr.DataArray(
            dilated_u8.astype(bool),
            dims=bad.dims,
            coords=bad.coords,
            attrs=bad.attrs,
        )

    # final keep-mask
    keep_mask = (~bad_dilated).astype(bool)

    # stats over spatial dims
    reduce_dims = [d for d in (ydim, xdim) if d in keep_mask.dims]
    per_slice_bad_original = bad.sum(dim=reduce_dims)
    per_slice_bad_buffered = bad_dilated.sum(dim=reduce_dims)
    per_slice_extra_masked = per_slice_bad_buffered - per_slice_bad_original

    total_bad_original = bad.sum()
    total_bad_buffered = bad_dilated.sum()
    total_extra_masked = total_bad_buffered - total_bad_original

    if compute_totals:
        try:
            from dask import compute as dask_compute
            tbo, tbb, tem = dask_compute(
                total_bad_original, total_bad_buffered, total_extra_masked
            )
            total_bad_original = int(np.asarray(tbo).item())
            total_bad_buffered = int(np.asarray(tbb).item())
            total_extra_masked = int(np.asarray(tem).item())
        except Exception:
            total_bad_original = int(np.asarray(total_bad_original).item())
            total_bad_buffered = int(np.asarray(total_bad_buffered).item())
            total_extra_masked = int(np.asarray(total_extra_masked).item())

    stats = {
        "total_bad_original": total_bad_original,
        "total_bad_buffered": total_bad_buffered,
        "total_extra_masked": total_extra_masked,
        "per_slice_bad_original": per_slice_bad_original,
        "per_slice_bad_buffered": per_slice_bad_buffered,
        "per_slice_extra_masked": per_slice_extra_masked,
    }

    return keep_mask, stats


def _infer_xy(ds):
    if {"y", "x"}.issubset(ds.dims):
        return "y", "x"
    if {"lat", "lon"}.issubset(ds.dims):
        return "lat", "lon"
    # fallback: assume last two non-time dims are spatial
    dims = [d for d in ds.dims if d != "time"]
    if len(dims) < 2:
        raise ValueError(f"Could not infer spatial dims from ds.dims={list(ds.dims)}")
    return dims[-2], dims[-1]
