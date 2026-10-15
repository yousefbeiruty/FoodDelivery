from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.models.entities import DeliveryStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=160)
    phone_number: str | None = Field(default=None, max_length=32)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    phone_number: str | None = Field(default=None, max_length=32)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    phone_number: str | None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MenuItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    restaurant_id: int
    name: str
    description: str
    price: float
    calories: int | None
    image_url: str | None
    category: str


class RestaurantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    rating: float
    delivery_time: str
    image_url: str | None
    category_tags: list[str]


class RestaurantMenu(RestaurantRead):
    menu_items: list[MenuItemRead]


class CartLine(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, le=100)


class QuoteRequest(BaseModel):
    items: list[CartLine] = Field(min_length=1)
    driver_tip: float = Field(default=0, ge=0, le=100)
    promo_code: str | None = Field(default=None, max_length=40)


class QuoteRead(BaseModel):
    subtotal: float
    delivery_fee: float
    driver_tip: float
    discount: float
    total_amount: float


class OrderCreate(QuoteRequest):
    delivery_address: str = Field(min_length=5, max_length=1000)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    menu_item_id: int
    name: str
    quantity: int
    unit_price: float


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    restaurant_id: int
    total_amount: float
    delivery_fee: float
    driver_tip: float
    discount: float
    promo_code: str | None
    delivery_status: DeliveryStatus
    delivery_address: str
    driver_name: str | None
    estimated_time: str | None
    driver_latitude: float | None
    driver_longitude: float | None
    created_at: datetime
    items: list[OrderItemRead]


class OrderStatusUpdate(BaseModel):
    delivery_status: DeliveryStatus
    driver_name: str | None = Field(default=None, max_length=160)
    estimated_time: str | None = Field(default=None, max_length=80)
    driver_latitude: float | None = Field(default=None, ge=-90, le=90)
    driver_longitude: float | None = Field(default=None, ge=-180, le=180)


class TrackingUpdate(BaseModel):
    order_id: int
    delivery_status: DeliveryStatus
    driver_name: str | None
    estimated_time: str | None
    driver_latitude: float | None
    driver_longitude: float | None
