"""Métricas canônicas sobre o snapshot tratado atual.

Este módulo não grava dados. Cada resposta carrega população, recorte e versão
para que interface, relatório e futura IA consultem a mesma fonte de verdade.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _current_snapshot() -> Path:
    pointer = json.loads((ROOT / "data_processed/current.json").read_text(encoding="utf-8"))
    target = (ROOT / pointer["path"]).resolve()
    processed = (ROOT / "data_processed").resolve()
    if not target.is_relative_to(processed):
        raise ValueError("snapshot fora de data_processed")
    return target


def _decimal(value: str | int | float) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True)
class Query:
    year: int = 2023
    month: int | None = None
    channel: str | None = None
    category: str | None = None


class Analytics:
    def __init__(self, snapshot: Path | None = None):
        self.snapshot = snapshot or _current_snapshot()
        self.version = json.loads((self.snapshot / "resumo.json").read_text(encoding="utf-8"))["snapshot"]
        with (self.snapshot / "vendas.csv").open(encoding="utf-8-sig", newline="") as stream:
            self.sales = list(csv.DictReader(stream))
        self.available_channels = sorted({row["canal"] for row in self.sales})
        self.available_categories = sorted({row["categoria"] for row in self.sales})
        self._validate()

    def _validate(self) -> None:
        required = {"order_id", "data_pedido", "canal", "categoria", "status_pagamento", "receita_liquida", "custo_produto", "custo_frete"}
        if not self.sales or not required.issubset(self.sales[0]):
            raise ValueError("snapshot de vendas incompatível com o contrato analítico")
        manifest = json.loads((self.snapshot / "manifest.json").read_text(encoding="utf-8"))
        import hashlib
        path = self.snapshot / "vendas.csv"
        expected = manifest["outputs"]["vendas.csv"]["sha256"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("hash do snapshot de vendas divergente")

    @staticmethod
    def _date(row: dict[str, str]):
        return row["data_pedido"][:10]

    def _rows(self, query: Query, approved_only: bool = True) -> list[dict[str, str]]:
        if query.year != 2023:
            raise ValueError("ano disponível no snapshot atual: 2023")
        if query.channel and query.channel not in self.available_channels:
            raise ValueError(f"canal não disponível: {query.channel}")
        if query.category and query.category not in self.available_categories:
            raise ValueError(f"categoria não disponível: {query.category}")
        rows = []
        for row in self.sales:
            if approved_only and row["status_pagamento"] != "Aprovado":
                continue
            date = self._date(row)
            if not date.startswith(f"{query.year:04d}-"):
                continue
            if query.month is not None and int(date[5:7]) != query.month:
                continue
            if query.channel and row["canal"] != query.channel:
                continue
            if query.category and row["categoria"] != query.category:
                continue
            rows.append(row)
        return rows

    @staticmethod
    def _aggregate(rows: list[dict[str, str]]) -> dict[str, Any]:
        revenue = sum((_decimal(row["receita_liquida"]) for row in rows), Decimal(0))
        margin = sum((_decimal(row["receita_liquida"]) - _decimal(row["custo_produto"]) - _decimal(row["custo_frete"]) for row in rows), Decimal(0))
        orders = len({row["order_id"] for row in rows})
        return {"orders": orders, "revenue": float(revenue), "margin": float(margin),
                "margin_pct": float(margin / revenue * 100) if revenue else None,
                "ticket": float(revenue / orders) if orders else None,
                "sample": len(rows)}

    def context(self, query: Query) -> dict[str, Any]:
        rows = self._rows(query)
        return {"snapshot": self.version, "population": "Aprovado; medidas completas", "year": query.year,
                "month": query.month, "channel": query.channel, "category": query.category,
                "metrics": self._aggregate(rows)}

    def health(self, query: Query = Query()) -> dict[str, Any]:
        return self.context(query)

    def trend(self, query: Query = Query()) -> dict[str, Any]:
        points = []
        months = [query.month] if query.month else list(range(1, 13))
        for month in months:
            point_query = Query(query.year, month, query.channel, query.category)
            points.append({"month": month, **self._aggregate(self._rows(point_query))})
        return {"context": {"snapshot": self.version, "population": "Aprovado; medidas completas", "year": query.year,
                             "channel": query.channel, "category": query.category}, "points": points}

    def channels(self, query: Query = Query()) -> dict[str, Any]:
        names = sorted({row["canal"] for row in self._rows(Query(query.year, query.month, None, query.category))})
        total = self._aggregate(self._rows(query))["revenue"]
        items = []
        for name in names:
            metrics = self._aggregate(self._rows(Query(query.year, query.month, name, query.category)))
            items.append({"channel": name, **metrics, "revenue_share_pct": metrics["revenue"] / total * 100 if total else None})
        items.sort(key=lambda item: item["revenue"], reverse=True)
        return {"context": self.context(query), "items": items}

    def evidence(self, query: Query = Query()) -> dict[str, Any]:
        aggregate = self._aggregate(self._rows(query))
        benchmark = self._aggregate(self._rows(Query(query.year, query.month, None, query.category)))
        return {"type": "descriptive", "context": self.context(query), "benchmark_margin_pct": benchmark["margin_pct"],
                "gap_margin_pp": aggregate["margin_pct"] - benchmark["margin_pct"] if aggregate["margin_pct"] is not None and benchmark["margin_pct"] is not None else None,
                "limitations": ["margem disponível não inclui comissões, impostos e outros custos econômicos", "gap diagnóstico não é saving", "observação não demonstra causalidade"]}


def query_from_params(params: dict[str, str]) -> Query:
    year = int(params.get("year", "2023"))
    month = params.get("month")
    month_int = int(month) if month not in (None, "", "all") else None
    if month_int is not None and month_int not in range(1, 13):
        raise ValueError("month deve estar entre 1 e 12")
    return Query(year=year, month=month_int, channel=params.get("channel") or None, category=params.get("category") or None)
