from pydantic import BaseModel, constr


class MetadataValidatorModel(BaseModel):
    key: constr(min_length=1, max_length=20)
    data: constr(min_length=1, max_length=90)


class MetadataKeyResponse(BaseModel):
    key: str

    class Config:
        orm_mode = True


class MetadataDataResponse(BaseModel):
    data: str

    class Config:
        orm_mode = True
