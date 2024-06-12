"""
Adapter and Quality Trimming using Trim Galore
"""

from modal import App

from rnaseqpipe.modules.utils import PLID
from rnaseqpipe.config import vol

app = App("rnaseq-trimgalore")


@app.function()
def trimgalore(plid: PLID):
    pass


@app.local_entrypoint()
def run():
    plid = PLID("pl-9e233179-57c0-43fb-b514-1f98745ceacb")

    #
    trimgalore.remote()
