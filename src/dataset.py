import torch
import numpy as np
import xarray as xr
from torch.utils.data import Dataset

class DEASentinel2Dataset(Dataset):
    BANDS = ["nbart_blue","nbart_green","nbart_red",
             "nbart_nir_2","nbart_swir_2","nbart_swir_3"]
    MEAN  = [343.4, 546.8, 444.1, 2942.5, 1444.6, 899.7]
    STD   = [255.0, 340.6, 373.0, 1232.4,  852.0, 680.1]

    def __init__(self, nc_path, patch_size=224, stride=112):
        self.ds         = xr.open_dataset(nc_path)
        self.patch_size = patch_size
        self.stride     = stride
        self.patches    = self._build_index()

    def _build_index(self):
        H = self.ds.sizes["y"]
        W = self.ds.sizes["x"]
        T = self.ds.sizes["time"]
        patches = []
        for t in range(T):
            for y in range(0, H - self.patch_size, self.stride):
                for x in range(0, W - self.patch_size, self.stride):
                    patches.append((t, y, x))
        return patches

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        t, y, x = self.patches[idx]
        P = self.patch_size
        arrays = []
        for i, band in enumerate(self.BANDS):
            arr = self.ds[band].isel(
                time=t,
                y=slice(y, y+P),
                x=slice(x, x+P),
            ).values.astype(np.float32)
            arr = np.nan_to_num(arr, nan=0.0)
            arr = (arr - self.MEAN[i]) / self.STD[i]
            arrays.append(arr)
        image = np.stack(arrays, axis=0)
        return {"image": torch.tensor(image, dtype=torch.float32)}
