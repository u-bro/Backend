from app.crud.base import CrudBase
from app.models import Coin
from app.schemas import CoinSchema


class CrudCoin(CrudBase):
    pass


coin_crud: CrudCoin = CrudCoin(Coin, CoinSchema)
