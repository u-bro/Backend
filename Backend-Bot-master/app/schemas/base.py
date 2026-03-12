from pydantic import ConfigDict, BaseModel, model_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    @model_validator(mode="after")
    def round_fare(self):
        actual_fare = getattr(self, "actual_fare", None)
        offer_fare = getattr(self, "offer_fare", None)
        expected_fare = getattr(self, "expected_fare", None)
        commission_amount = getattr(self, "commission_amount", None)
        amount = getattr(self, "amount", None)
        fixed_amount = getattr(self, "fixed_amount", None)

        if not actual_fare and not offer_fare and not expected_fare and not commission_amount and not amount and not fixed_amount:
            return self

        if actual_fare is not None:
            setattr(self, "actual_fare", round(actual_fare, 2))
        if offer_fare is not None:
            setattr(self, "offer_fare", round(offer_fare, 2))
        if expected_fare is not None:
            setattr(self, "expected_fare", round(expected_fare, 2))
        if commission_amount is not None:
            setattr(self, "commission_amount", round(commission_amount, 2))
        if amount is not None:
            setattr(self, "amount", round(amount, 2))
        if fixed_amount is not None:
            setattr(self, "fixed_amount", round(fixed_amount, 2))
        return self