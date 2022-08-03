from typing import Any, List, Tuple

import torch
import torch.nn as nn
from pytorch_lightning import LightningModule
from torch.autograd import Variable

from src.models.components.conv_block import ConvBlock
from src.utils.metrics import rmse, rsquared, smape


class RCNNModule(LightningModule):
    """Example of LightningModule for MNIST classification.

    A LightningModule organizes your PyTorch code into 5 sections:
        - Computations (init).
        - Train loop (training_step)
        - Validation loop (validation_step)
        - Test loop (test_step)
        - Optimizers (configure_optimizers)

    Read the docs:
        https://pytorch-lightning.readthedocs.io/en/latest/common/lightning_module.html
    """

    def __init__(
        self,
        embedding_size: int = 16,
        hidden_state_size: int = 32,
        n_cells_hor: int = 200,
        n_cells_ver: int = 250,
        batch_size: int = 1,
    ):
        super(self.__class__, self).__init__()

        # this line allows to access init params with 'self.hparams' attribute
        # it also ensures init params will be stored in ckpt
        self.save_hyperparameters(logger=False)

        self.n_cells_hor = n_cells_hor
        self.n_cells_ver = n_cells_ver
        self.batch_size = batch_size

        self.emb_size = embedding_size
        self.hid_size = hidden_state_size

        self.embedding = nn.Sequential(
            ConvBlock(1, self.emb_size, 3),
            nn.ReLU(),
            ConvBlock(self.emb_size, self.emb_size, 3),
        )
        self.hidden_to_result = nn.Sequential(
            ConvBlock(hidden_state_size, 2, kernel_size=3),
            nn.Softmax(dim=1),
        )

        self.f_t = nn.Sequential(
            ConvBlock(self.hid_size + self.emb_size, self.hid_size, 3), nn.Sigmoid()
        )
        self.i_t = nn.Sequential(
            ConvBlock(self.hid_size + self.emb_size, self.hid_size, 3), nn.Sigmoid()
        )
        self.c_t = nn.Sequential(
            ConvBlock(self.hid_size + self.emb_size, self.hid_size, 3), nn.Tanh()
        )
        self.o_t = nn.Sequential(
            ConvBlock(self.hid_size + self.emb_size, self.hid_size, 3), nn.Sigmoid()
        )

        self.final_conv = nn.Sequential(
            nn.Conv2d(
                self.hid_size,
                self.hid_size,
                kernel_size=3,
                stride=1,
                padding=1,
                bias=False,
            ),
            nn.ReLU(),
            nn.Conv2d(self.hid_size, 1, kernel_size=1, stride=1, padding=0, bias=False),
        )

        self.prev_state = (
            Variable(
                torch.zeros(
                    self.batch_size, self.hid_size, self.n_cells_hor, self.n_cells_ver
                )
            ),
            Variable(
                torch.zeros(
                    batch_size, self.hid_size, self.n_cells_hor, self.n_cells_ver
                )
            ),
        )

        # use separate metric instance for train, val and test step
        # to ensure a proper reduction over the epoch
        self.train_metric = rsquared()
        self.val_metric = rsquared()
        self.test_metric = rsquared()


        # loss
        self.criterion = nn.MSELoss()

    def forward(self, x: torch.Tensor, prev_state: Tuple[torch.Tensor]):
        (prev_c, prev_h) = prev_state
        x_emb = self.embedding(x)
        x_and_h = torch.cat([prev_h, x_emb], dim=1)

        f_i = self.f_t(x_and_h)
        i_i = self.i_t(x_and_h)
        c_i = self.c_t(x_and_h)
        o_i = self.o_t(x_and_h)

        next_c = prev_c * f_i + i_i * c_i
        next_h = torch.tanh(next_c) * o_i

        assert prev_h.shape == next_h.shape
        assert prev_c.shape == next_c.shape

        prediction = self.final_conv(next_h)

        return (next_c, next_h), prediction


    def step(self, batch: Any):
        x, y = batch
        self.prev_state, preds = self.forward(x, self.prev_state)
        loss = self.criterion(preds, y)
        return loss, preds, y

    def training_step(self, batch: Any, batch_idx: int):
        loss, preds, targets = self.step(batch)

        # log train metrics
        train_metric = self.train_metric(preds, targets)
        self.log("train/loss", loss, on_step=False, on_epoch=True, prog_bar=True)
        self.log("train/R2", train_metric, on_step=False, on_epoch=True, prog_bar=True)

        # we can return here dict with any tensors
        # and then read it in some callback or in `training_epoch_end()`` below
        # remember to always return loss from `training_step()` or else backpropagation will fail!
        return {"loss": loss, "preds": preds, "targets": targets}

    def training_epoch_end(self, outputs: List[Any]):
        # `outputs` is a list of dicts returned from `training_step()`
        pass

    def validation_step(self, batch: Any, batch_idx: int):
        loss, preds, targets = self.step(batch)

        # log val metrics
        val_metric = self.val_metric(preds, targets)
        self.log("val/loss", loss, on_step=False, on_epoch=True, prog_bar=True)
        self.log("val/acc", val_metric, on_step=False, on_epoch=True, prog_bar=True)

        return {"loss": loss, "preds": preds, "targets": targets}

    def validation_epoch_end(self, outputs: List[Any]):
        pass

    def test_step(self, batch: Any, batch_idx: int):
        loss, preds, targets = self.step(batch)

        # log test metrics
        test_metric= self.test_metric(preds, targets)
        self.log("test/loss", loss, on_step=False, on_epoch=True)
        self.log("test/acc", test_metric, on_step=False, on_epoch=True)

        return {"loss": loss, "preds": preds, "targets": targets}

    def test_epoch_end(self, outputs: List[Any]):
        pass

    def on_epoch_end(self):
        pass

    def configure_optimizers(self):
        """Choose what optimizers and learning-rate schedulers to use in your optimization.
        Normally you'd need one. But in the case of GANs or similar you might have multiple.

        See examples here:
            https://pytorch-lightning.readthedocs.io/en/latest/common/lightning_module.html#configure-optimizers
        """
        return torch.optim.Adam(
            params=self.parameters(),
            lr=self.hparams.lr,
            weight_decay=self.hparams.weight_decay,
        )