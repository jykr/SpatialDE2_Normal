from typing import List, Optional, Union

import numpy as np
import tensorflow as tf

from anndata import AnnData


class AnnDataIterator:
    def __init__(
        self,
        adata: AnnData,
        genes: Optional[List[str]] = None,
        layer: Optional[str] = None,
        dtype: Optional[Union[np.dtype, tf.DType]] = None,
    ):
        self.adata = adata
        self.genes = genes
        if self.genes is None:
            self.genes = self.adata.var_names
        self.layer = layer
        if dtype is not None:
            outtype = dtype
        elif self.layer is None:
            outtype = self.adata.X.dtype
        else:
            outtype = self.adata.layers[layer].dtype
        self.output_types = (outtype, tf.string)

    def __call__(self):
        for g in self.genes:
            slice = self.adata[:, g]
            if self.layer is None:
                data = np.squeeze(slice.X)
            else:
                data = np.squeeze(slice.layers[self.layer])
            with tf.device(tf.DeviceSpec(device_type="CPU").to_string()):
                gene = tf.convert_to_tensor(g)
            yield tf.convert_to_tensor(data, dtype=self.output_types[0]), gene


class AnnDataDataset(tf.data.Dataset):
    def __new__(
        cls,
        adata: AnnData,
        genes: Optional[List[str]] = None,
        layer: Optional[str] = None,
        dtype: Optional[Union[np.dtype, tf.DType]] = None,
    ):
        it = AnnDataIterator(adata, genes, layer, dtype)
        return (
            tf.data.Dataset.from_generator(it, output_types=it.output_types)
            .repeat(1)
            .prefetch(tf.data.experimental.AUTOTUNE)
        )
