from typing import List
from fastapi import Request, Depends, HTTPException
from pydantic import TypeAdapter
from app.backend.routers.base import BaseRouter
from app.crud.ride import ride_crud
from app.models import Ride
from app.schemas.ride import RideSchema, RideSchemaIn, RideSchemaCreate, RideSchemaUpdateByClient, RideSchemaUpdateByDriver, RideSchemaFinishWithAnomaly, RideSchemaFinishByDriver, RideSchemaAcceptByDriver
from app.backend.deps import require_role, get_current_user_id, get_current_driver_profile_id, require_owner, require_driver_profile
from app.models import Ride
from app.services import pdf_generator
from app.crud import document_crud


class RideRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__(ride_crud, "/rides")

    def setup_routes(self) -> None:
        self.router.add_api_route(f"{self.prefix}", self.get_paginated, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}", self.create, methods=["POST"], status_code=201, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.get_by_id, methods=["GET"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.update, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}", self.delete, methods=["DELETE"], status_code=202, dependencies=[Depends(require_role(["admin"]))])
        
        self.router.add_api_route(f"{self.prefix}/{{id}}/client", self.update_by_client, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["user", "driver", "admin"])), Depends(require_owner(Ride, 'client_id'))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/driver", self.update_by_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"])), Depends(require_driver_profile(Ride))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/accept", self.accept_ride, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])
        self.router.add_api_route(f"{self.prefix}/{{id}}/finish", self.finish_ride_by_driver, methods=["PUT"], status_code=200, dependencies=[Depends(require_role(["driver", "admin"]))])

    async def get_paginated(self, request: Request, page: int = 1, page_size: int = 10) -> list[RideSchema]:
        items = await super().get_paginated(request, page, page_size)
        return TypeAdapter(List[RideSchema]).validate_python(items)

    async def get_by_id(self, request: Request, id: int) -> RideSchema:
        return await super().get_by_id(request, id)

    async def create(self, request: Request, create_obj: RideSchemaIn, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        create_obj = RideSchemaCreate(client_id=user_id, **create_obj.model_dump())
        return await super().create(request, create_obj)

    async def update(self, request: Request, id: int, update_obj: RideSchema, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        return await self.model_crud.update(request.state.session, id, update_obj, user_id)

    async def delete(self, request: Request, id: int) -> RideSchema:
        return await super().delete(request, id)

    async def update_by_client(self, request: Request, id: int, update_obj: RideSchemaUpdateByClient, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        return await self.model_crud.update(request.state.session, id, update_obj, user_id)

    async def accept_ride(self, request: Request, id: int, update_obj: RideSchemaAcceptByDriver, driver_profile_id: int = Depends(get_current_driver_profile_id), user_id: int = Depends(get_current_user_id)) -> RideSchema:
        update_obj = RideSchemaAcceptByDriver(driver_profile_id=driver_profile_id, **update_obj.model_dump(exclude={"driver_profile_id"}),)
        accepted = await self.model_crud.accept(request.state.session, id, update_obj, user_id)
        if accepted is not None:
            return accepted

        existing = await self.model_crud.get_by_id(request.state.session, id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Ride not found")
        raise HTTPException(status_code=409, detail="Ride already accepted")

    async def update_by_driver(self, request: Request, id: int, update_obj: RideSchemaUpdateByDriver, user_id: int = Depends(get_current_user_id)) -> RideSchema:
        return await self.model_crud.update(request.state.session, id, update_obj, user_id)

    async def finish_ride_by_driver(self, request: Request, id: int, update_obj: RideSchemaFinishByDriver, ride: Ride = Depends(require_driver_profile(Ride)), user_id: int = Depends(get_current_user_id)) -> RideSchema:
        update_obj = RideSchemaFinishWithAnomaly(is_anomaly=str(ride.expected_fare) != str(update_obj.actual_fare), **update_obj.model_dump())
        return await self.model_crud.update(request.state.session, id, update_obj, user_id)
    async def finish_ride_by_driver(self, request: Request, id: int, update_obj: RideSchemaFinishByDriver, ride: Ride = Depends(require_driver_profile(Ride))) -> RideSchema:
        # key = f"receipts/rides/{id}/receipt.pdf"
        # pdf_check = await pdf_generator.generate_ride_receipt(id, str(ride.client_id), str(ride.driver_profile_id), ride.pickup_address, ride.dropoff_address, update_obj.actual_fare, ride.distance_meters / 1000, ride.duration_seconds / 60)
        # await document_crud.upload_pdf_bytes(key, pdf_check)
        
        update_obj = RideSchemaFinishWithAnomaly(is_anomaly=str(ride.expected_fare) != str(update_obj.actual_fare), ride_metadata={"receipt_s3_key": key}, **update_obj.model_dump())
        return await super().update(request, id, update_obj)


ride_router = RideRouter().router
