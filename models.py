from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    quotes = relationship("Quote", back_populates="user")

class Lane(Base):
    __tablename__ = "lanes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origem: Mapped[str] = mapped_column(String(120), nullable=False)
    destino: Mapped[str] = mapped_column(String(120), nullable=False)
    regiao: Mapped[str] = mapped_column(String(120), nullable=True)

    min_ate_10kg: Mapped[float] = mapped_column(Float, nullable=False)
    kg_excedente: Mapped[float] = mapped_column(Float, nullable=False)

    adval_percent: Mapped[float] = mapped_column(Float, nullable=False)   # ex.: 0.9 (percentual)
    adval_min: Mapped[float] = mapped_column(Float, nullable=False)

    cubagem_kg_m3: Mapped[float] = mapped_column(Float, nullable=False)   # ex.: 300
    icms: Mapped[str] = mapped_column(String(120), nullable=True)
    observacao: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("origem", "destino", name="uq_origem_destino"),
        Index("ix_lane_origem", "origem"),
        Index("ix_lane_destino", "destino"),
    )

class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    origem: Mapped[str] = mapped_column(String(120), nullable=False)
    destino: Mapped[str] = mapped_column(String(120), nullable=False)

    peso_real_kg: Mapped[float] = mapped_column(Float, nullable=False)
    volume_m3: Mapped[float] = mapped_column(Float, nullable=False)
    valor_mercadoria: Mapped[float] = mapped_column(Float, nullable=False)

    cubagem_kg_m3: Mapped[float] = mapped_column(Float, nullable=False)
    peso_cubado_kg: Mapped[float] = mapped_column(Float, nullable=False)
    peso_tarifavel_kg: Mapped[float] = mapped_column(Float, nullable=False)

    frete_base: Mapped[float] = mapped_column(Float, nullable=False)
    advalorem: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)

    detalhes_json: Mapped[str] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="quotes")
