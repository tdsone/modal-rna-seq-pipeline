class PLID:
    def __init__(self, id: str = None) -> None:
        if id is None:
            self.id = self._generate_pipeline_id()
        else:
            self.id = id

    def _generate_pipeline_id(self):
        from uuid import uuid4

        id = uuid4()

        return f"pl-{id}"

    def __str__(self) -> str:
        return self.id
