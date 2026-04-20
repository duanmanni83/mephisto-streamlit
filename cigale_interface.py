"""
CIGALE Interface Module for Mephisto Streamlit App

This module provides a Python interface to run CIGALE (pcigale) from within
the Streamlit application. It handles configuration generation, execution,
and result parsing.
"""

import os
import tempfile
import subprocess
import numpy as np
import pandas as pd
from astropy.io import fits
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json


class CigaleRunner:
    """
    Runner class to execute CIGALE SED fitting.
    """

    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize CIGALE runner.

        Args:
            work_dir: Working directory for CIGALE. If None, creates a temp directory.
        """
        if work_dir is None:
            self.work_dir = tempfile.mkdtemp(prefix="cigale_")
        else:
            self.work_dir = work_dir
            os.makedirs(self.work_dir, exist_ok=True)

        self.config_file = os.path.join(self.work_dir, "pcigale.ini")
        self.data_file = os.path.join(self.work_dir, "input_data.txt")
        self.output_dir = os.path.join(self.work_dir, "out")

    def create_input_data(
        self,
        object_id: str,
        redshift: float,
        photometry: Dict[str, float],
        photometry_err: Optional[Dict[str, float]] = None
    ) -> pd.DataFrame:
        """
        Create input data file for CIGALE.

        Args:
            object_id: Object identifier
            redshift: Redshift value
            photometry: Dictionary of {filter_name: flux_in_mJy}
            photometry_err: Dictionary of {filter_name: error_in_mJy}

        Returns:
            DataFrame with the input data
        """
        data = {'id': [object_id], 'redshift': [redshift]}

        for band, flux in photometry.items():
            data[band] = [flux]
            if photometry_err and band in photometry_err:
                data[f"{band}_err"] = [photometry_err[band]]
            else:
                # Default 10% error
                data[f"{band}_err"] = [flux * 0.1]

        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep=' ', index=False)

        return df

    def create_config(
        self,
        sed_modules: List[str],
        module_params: Optional[Dict[str, Dict[str, Any]]] = None,
        analysis_method: str = "savefluxes",
        cores: int = 4
    ) -> str:
        """
        Create pcigale.ini configuration file.

        Args:
            sed_modules: List of SED module names in order
            module_params: Dictionary of module parameters
            analysis_method: 'savefluxes' or 'pdf_analysis'
            cores: Number of CPU cores to use

        Returns:
            Path to the configuration file
        """
        if module_params is None:
            module_params = {}

        config_lines = [
            f"data_file = {self.data_file}",
            f"parameters_file = ",
            f"sed_modules = {', '.join(sed_modules)}",
            f"analysis_method = {analysis_method}",
            f"cores = {cores}",
            "",
            "[sed_modules_params]",
            ""
        ]

        # Add module-specific parameters
        for module in sed_modules:
            config_lines.append(f"  [[{module}]]")
            if module in module_params:
                for param, value in module_params[module].items():
                    config_lines.append(f"    {param} = {value}")
            else:
                # Add default parameters
                defaults = self._get_default_params(module)
                for param, value in defaults.items():
                    config_lines.append(f"    {param} = {value}")
            config_lines.append("")

        # Add analysis parameters
        config_lines.extend([
            "",
            "[analysis_params]",
            "  variables = ",
            "  save_sed = True",
            "  blocks = 1"
        ])

        config_content = "\n".join(config_lines)

        with open(self.config_file, 'w') as f:
            f.write(config_content)

        return self.config_file

    def _get_default_params(self, module: str) -> Dict[str, Any]:
        """Get default parameters for a given module."""
        defaults = {
            "sfhdelayed": {
                "tau_main": 5000,
                "age_main": 7000,
                "tau_burst": 50,
                "age_burst": 20,
                "f_burst": 0.0,
                "sfr_A": 1.0,
                "normalise": True
            },
            "sfh2exp": {
                "tau_main": 5000,
                "age_main": 7000,
                "tau_burst": 50,
                "age_burst": 20,
                "f_burst": 0.0,
                "sfr_A": 1.0,
                "normalise": True
            },
            "bc03": {
                "imf": 0,  # Salpeter
                "metallicity": 0.02,
                "separation_age": 10
            },
            "cb19": {
                "imf": 1,  # Chabrier
                "metallicity": 0.02,
                "separation_age": 10
            },
            "m2005": {
                "imf": 0,  # Salpeter
                "metallicity": 0.02,
                "separation_age": 10
            },
            "nebular": {
                "logU": -2.0,
                "zgas": 0.02,
                "ne": 100,
                "f_esc": 0.0,
                "f_dust": 0.0,
                "lines_width": 300.0,
                "emission": True
            },
            "dustatt_modified_CF00": {
                "Av_ISM": 1.0,
                "mu": 0.44,
                "slope_ISM": -0.7,
                "slope_BC": -1.3,
                "filters": "galex.FUV & generic.bessell.B & generic.bessell.V"
            },
            "dustatt_modified_starburst": {
                "E_BV": 0.3,
                "R_V": 4.05,
                "filters": "galex.FUV & generic.bessell.B & generic.bessell.V"
            },
            "dl2007": {
                "qpah": 2.5,
                "umin": 1.0,
                "umax": 1000000.0,
                "gamma": 0.1
            },
            "dl2014": {
                "qpah": 2.5,
                "umin": 1.0,
                "umax": 1000000.0,
                "gamma": 0.1
            },
            "dale2014": {
                "alpha": 2.0,
                "beta": 1.0
            },
            "casey2012": {
                "temperature": 50.0,
                "beta": 1.5,
                "alpha": 2.0
            },
            "redshifting": {
                "redshift": ""
            },
            "fritz2006": {
                "r_ratio": 60.0,
                "tau": 1.0,
                "beta": -0.5,
                "gamma": 4.0,
                "opening_angle": 100.0,
                "psy": 0.001,
                "fractal_clouds": 0.0,
                "albedo": 0.037,
                "fraction": 0.5
            },
            "skirtor2016": {
                "t": 5.0,
                "pl": 1.0,
                "q": 1.0,
                "oa": 40.0,
                "R": 20.0,
                "Mcl": 0.97,
                "i": 30.0,
                "fracAGN": 0.0
            },
            "restframe_parameters": {
                "beta_calz94": False,
                "D4000": False,
                "IRX": False,
                "EW_lines": "500.7/1.0 & 656.3/1.0"
            }
        }

        return defaults.get(module, {})

    def generate_config(self) -> bool:
        """Generate full configuration using pcigale genconf."""
        try:
            result = subprocess.run(
                ["pcigale", "genconf"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error generating config: {e}")
            return False

    def run(self) -> Tuple[bool, str]:
        """
        Run CIGALE.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate full configuration
            if not self.generate_config():
                return False, "Failed to generate configuration"

            # Run CIGALE
            result = subprocess.run(
                ["pcigale", "run"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                return True, "CIGALE completed successfully"
            else:
                return False, f"CIGALE failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "CIGALE timed out after 5 minutes"
        except Exception as e:
            return False, f"Error running CIGALE: {str(e)}"

    def get_results(self) -> Optional[pd.DataFrame]:
        """
        Get CIGALE results as a DataFrame.

        Returns:
            DataFrame with results or None if not available
        """
        results_file = os.path.join(self.output_dir, "models-block-0.txt")
        fits_file = os.path.join(self.output_dir, "models-block-0.fits")

        if os.path.exists(results_file):
            return pd.read_csv(results_file, sep=r'\s+')
        elif os.path.exists(fits_file):
            with fits.open(fits_file) as hdul:
                data = hdul[1].data
                return pd.DataFrame(data)

        return None

    def get_sed(self, model_index: int = 0) -> Optional[Dict[str, np.ndarray]]:
        """
        Get SED data for a specific model.

        Note: This requires save_sed=True in analysis_params.
        SED data is stored in the FITS file when using savefluxes.

        Args:
            model_index: Index of the model to retrieve

        Returns:
            Dictionary with 'wavelength', 'flux', 'attenuation' arrays
        """
        fits_file = os.path.join(self.output_dir, "models-block-0.fits")

        if not os.path.exists(fits_file):
            return None

        try:
            with fits.open(fits_file) as hdul:
                # SED data is typically in extension 2 or later
                if len(hdul) > 2:
                    sed_data = hdul[2 + model_index].data
                    return {
                        'wavelength': sed_data['WAVELENGTH'],
                        'flux': sed_data['FLUX'],
                        'attenuation': sed_data.get('ATTENUATION', np.zeros_like(sed_data['FLUX']))
                    }
        except Exception as e:
            print(f"Error reading SED: {e}")

        return None

    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.work_dir) and self.work_dir.startswith(tempfile.gettempdir()):
            shutil.rmtree(self.work_dir)


# Predefined filter sets for common instruments
FILTER_SETS = {
    "SDSS": ["sdss.u", "sdss.g", "sdss.r", "sdss.i", "sdss.z"],
    "GALEX": ["galex.FUV", "galex.NUV"],
    "2MASS": ["2mass.J", "2mass.H", "2mass.Ks"],
    "WISE": ["wise.W1", "wise.W2", "wise.W3", "wise.W4"],
    "HERSCHEL": ["herschel.PACS.100", "herschel.PACS.160", "herschel.SPIRE.250", "herschel.SPIRE.350", "herschel.SPIRE.500"],
    "JWST_NIRCAM": ["jwst.nircam.F070W", "jwst.nircam.F090W", "jwst.nircam.F115W", "jwst.nircam.F150W", "jwst.nircam.F200W", "jwst.nircam.F277W", "jwst.nircam.F356W", "jwst.nircam.F444W"],
    "HST_ACS": ["hst.acs.f435w", "hst.acs.f475w", "hst.acs.f555w", "hst.acs.f606w", "hst.acs.f625w", "hst.acs.f775w", "hst.acs.f814w", "hst.acs.f850lp"]
}

# Module categories
MODULE_CATEGORIES = {
    "SFH": ["sfh2exp", "sfhdelayed", "sfhdelayedbq", "sfhfromfile", "sfhperiodic"],
    "SSP": ["bc03", "cb19", "bpassv2", "m2005"],
    "Nebular": ["nebular"],
    "Dust Attenuation": ["dustatt_modified_CF00", "dustatt_modified_starburst", "dustatt_2powerlaws", "dustatt_powerlaw"],
    "Dust Emission": ["casey2012", "dale2014", "dl2007", "dl2014", "themis"],
    "AGN": ["fritz2006", "skirtor2016"],
    "X-ray": ["yang20", "lopez24"],
    "Radio": ["radio"],
    "Redshifting": ["redshifting"],
    "Restframe": ["restframe_parameters"]
}


def run_simple_sed(
    redshift: float,
    filters: List[str],
    fluxes: List[float],
    flux_errors: Optional[List[float]] = None,
    sfh_module: str = "sfhdelayed",
    ssp_module: str = "bc03",
    dust_module: str = "dustatt_modified_CF00",
    dust_emission_module: Optional[str] = "dl2007",
    use_nebular: bool = True,
    use_agn: bool = False,
    **module_params
) -> Dict[str, Any]:
    """
    Run a simple SED fit with CIGALE.

    This is a convenience function for quick SED fitting.

    Args:
        redshift: Object redshift
        filters: List of filter names
        fluxes: List of flux values in mJy
        flux_errors: Optional list of flux errors
        sfh_module: SFH module name
        ssp_module: SSP module name
        dust_module: Dust attenuation module name
        dust_emission_module: Dust emission module name (optional)
        use_nebular: Include nebular emission
        use_agn: Include AGN component
        **module_params: Additional module parameters

    Returns:
        Dictionary with results
    """
    runner = CigaleRunner()

    # Create photometry dictionary
    photometry = {f: fluxes[i] for i, f in enumerate(filters)}
    photometry_err = None
    if flux_errors:
        photometry_err = {f: flux_errors[i] for i, f in enumerate(filters)}

    # Create input data
    runner.create_input_data("object_1", redshift, photometry, photometry_err)

    # Build module list
    modules = [sfh_module, ssp_module]
    if use_nebular:
        modules.append("nebular")
    modules.append(dust_module)
    if dust_emission_module:
        modules.append(dust_emission_module)
    if use_agn:
        modules.append("skirtor2016")
    modules.append("redshifting")

    # Create configuration
    runner.create_config(modules, module_params)

    # Run CIGALE
    success, message = runner.run()

    results = {
        "success": success,
        "message": message,
        "work_dir": runner.work_dir
    }

    if success:
        df = runner.get_results()
        if df is not None:
            results["data"] = df.to_dict()

        sed = runner.get_sed()
        if sed:
            results["sed"] = sed

    return results
