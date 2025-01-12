"""
This module defines the `SlidingRadial` class, which implements a sliding radial perturbation
on input images.
"""

from typing import Any, Optional

import numpy as np
from scipy.ndimage.filters import gaussian_filter
from skimage.draw import ellipse

from xaitk_saliency.interfaces.perturb_image import PerturbImage


class SlidingRadial(PerturbImage):
    """
    Produce perturbation matrices generated by sliding a radial occlusion area
    with configured radius over the area of an image. When the two radius values
    are the same, circular masks are generated; otherwise, elliptical masks are
    generated. Passing sigma values will apply a Gaussian filter to the mask,
    blurring it. This results in a smooth transition from full occlusion in the
    center of the radial to no occlusion at the edge.

    Due to the geometry of sliding radials, if the stride given does not evenly
    divide the radial size along the applicable axis, then the result plane of
    values when summing the generated masks will not be even.

    Related, if the stride is set to be larger than the radial diameter, the
    resulting plane of summed values will also not be even, as there be
    increasingly long valleys of unperturbed space between masked regions.

    The generated masks are boolean if no blurring is used, otherwise the masks
    will be of floating-point type in the [0, 1] range.
    """

    def __init__(
        self,
        radius: tuple[float, float] = (50, 50),
        stride: tuple[int, int] = (20, 20),
        sigma: Optional[tuple[float, float]] = None,
    ) -> None:
        """
        Produce perturbation matrices generated by sliding a radial occlusion area
        with configured radius over the area of an image.

        :param radius: The radius of the occlusion area in pixels as a tuple with
            format `(radius_y, radius_x)`.
        :param stride: The striding step in pixels for the center of the radial as
            a tuple with format `(height_step, width_step)`.
        :param sigma: The sigma values for the Gaussian filter applied to masks in
            pixels as a tuple with format `(sigma_y, sigma_x)`.
        """
        self.radius = (radius[0], radius[1])
        self.stride = (int(stride[0]), int(stride[1]))
        self.sigma = (sigma[0], sigma[1]) if sigma else None

    def perturb(self, ref_image: np.ndarray) -> np.ndarray:
        """
        Produce a mask based on a radial occlusion area
        with configured radius over the area of an image

        :param ref_image:
            Reference image to generate perturbations from.
        :return: Mask matrix with shape [nMasks x Height x Width].
        """
        stride_h, stride_w = self.stride
        img_h, img_w = ref_image.shape[:2]
        center_xs = np.arange(0, img_w, stride_w)
        center_ys = np.arange(0, img_h, stride_h)

        num_masks = len(center_xs) * len(center_ys)
        masks = np.zeros((num_masks, img_h, img_w), dtype="float32" if self.sigma else "bool")
        center_xs_m = np.tile(center_xs, len(center_ys))
        center_ys_m = np.repeat(center_ys, len(center_xs))

        for i, (center_x, center_y) in enumerate(zip(center_xs_m, center_ys_m)):
            mask = masks[i]
            coords = ellipse(center_y, center_x, *self.radius, shape=mask.shape)
            mask[coords] = 1

            if self.sigma:
                mask[:] = gaussian_filter(mask, sigma=self.sigma)
                mask[:] = mask / mask.max()

            mask[:] = 1 - mask if self.sigma else ~mask

        return masks

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """
        Returns the default configuration for the SlidingRadial.

        This method provides a default configuration dictionary, specifying default
        values for key parameters in the factory. It can be used to create an instance
        of the factory with preset configurations.

        Returns:
            dict[str, Any]: A dictionary containing default configuration parameters.
        """
        # Minor override to curry tuple defaults into lists, which are the
        # JSON-parsed types. This is to allow successful equality between
        # default, get_config() and JSON-parsed outputs.
        cfg = super().get_default_config()
        cfg["radius"] = list(cfg["radius"])
        cfg["stride"] = list(cfg["stride"])
        return cfg

    def get_config(self) -> dict[str, Any]:
        """
        Get the configuration dictionary of the SlidingRadial instance.

        Returns:
            dict[str, Any]: Configuration dictionary.
        """
        return {
            "radius": list(self.radius),
            "stride": list(self.stride),
            "sigma": list(self.sigma) if self.sigma else None,
        }
