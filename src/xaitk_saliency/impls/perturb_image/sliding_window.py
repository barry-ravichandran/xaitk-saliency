from typing import Any

import numpy as np

from xaitk_saliency.interfaces.perturb_image import PerturbImage


class SlidingWindow(PerturbImage):
    """
    Produce perturbation  matrices based on hard, block-y occlusion areas as
    generated by sliding a window of a configured size over the area of an
    image.

    Due to the geometry of sliding windows, if the stride given does not evenly
    divide the window size along the applicable axis, then the result plane of
    values when summing the generated masks will not be even.

    Related, if the stride is set to be larger than the window size, the
    resulting plane of summed values will also not be even, as there be
    increasingly long valleys of unperturbed space between masked regions.

    :param window_size: The block window size in pixels as a tuple with format
        `(height, width)`.
    :param stride: The sliding window striding step in pixels as a tuple with
        format `(height_step, width_step)`.
    """

    def __init__(
        self,
        window_size: tuple[int, int] = (50, 50),
        stride: tuple[int, int] = (20, 20),
    ) -> None:
        self.window_size: tuple[int, int] = (int(window_size[0]), int(window_size[1]))
        self.stride: tuple[int, int] = (int(stride[0]), int(stride[1]))

    def perturb(self, ref_image: np.ndarray) -> np.ndarray:
        win_h, win_w = self.window_size
        stride_h, stride_w = self.stride
        img_size = ref_image.shape[:2]
        img_h, img_w = img_size

        rows = np.arange(0, img_h, stride_h)
        cols = np.arange(0, img_w, stride_w)

        # Overhang of last window.
        overhang_h = win_h - (img_h - rows[-1])
        overhang_w = win_w - (img_w - cols[-1])

        # Offset rows and cols to center windows.
        rows -= overhang_h // 2
        cols -= overhang_w // 2

        num_masks = len(rows) * len(cols)
        masks = np.ones((num_masks, img_h, img_w), dtype=bool)
        rows_m = np.repeat(rows, len(cols))
        cols_m = np.tile(cols, len(rows))

        for i, (r, c) in enumerate(zip(rows_m, cols_m)):
            # use of np.clip function here is more costly than min/max use.
            r1 = max(0, r)
            r2 = min(r + win_h, img_h)
            c1 = max(0, c)
            c2 = min(c + win_w, img_w)
            rs = slice(r1, r2)
            cs = slice(c1, c2)
            masks[i, rs, cs] = False

        return masks

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        # Minor override to curry tuple defaults into lists, which are the
        # JSON-parsed types. This is to allow successful equality between
        # default, get_config() and JSON-parsed outputs.
        cfg = super().get_default_config()
        cfg["window_size"] = list(cfg["window_size"])
        cfg["stride"] = list(cfg["stride"])
        return cfg

    def get_config(self) -> dict[str, Any]:
        return {
            "window_size": list(self.window_size),
            "stride": list(self.stride),
        }