import io

import numpy as np
from netCDF4 import Dataset

from ingestion.netcdf_ingest import parse_netcdf_file


def test_netcdf_normalizes_optional_bgc_variables(tmp_path):
    path = tmp_path / "argo.nc"
    dataset = Dataset(path, "w")
    dataset.createDimension("N_PROF", 1)
    dataset.createDimension("N_LEVELS", 2)
    dataset.createVariable("PLATFORM_NUMBER", "i4", ("N_PROF",))[:] = [5900001]
    dataset.createVariable("JULD", "f8", ("N_PROF",))[:] = [26784]
    dataset.createVariable("LATITUDE", "f4", ("N_PROF",))[:] = [5]
    dataset.createVariable("LONGITUDE", "f4", ("N_PROF",))[:] = [72]
    dataset.createVariable("PRES", "f4", ("N_LEVELS",))[:] = [0, 500]
    dataset.createVariable("TEMP", "f4", ("N_LEVELS",))[:] = [29, 10]
    dataset.createVariable("DOXY", "f4", ("N_LEVELS",))[:] = [200, 40]
    dataset.close()
    upload = io.BytesIO(path.read_bytes())
    upload.name = "argo.nc"
    frame, metadata = parse_netcdf_file(upload)
    assert len(frame) == 2
    assert "oxygen" in frame.columns
    assert metadata["float_count"] == 1
    assert metadata["measurements_count"] == 2
