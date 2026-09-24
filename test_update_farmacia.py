import unittest
import csv
import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from main import (
    exportar_medicamentos_csv,
    exportar_medicamentos_farmacia_csv,
    update_medicamento_farmacia,
)
from models import Medicamento, MedicamentoFarmacia
from schemas import MedicamentoUpdate


VALID_ID = "507f1f77bcf86cd799439011"


class UpdateMedicamentoFarmaciaTests(unittest.IsolatedAsyncioTestCase):
    async def test_updates_only_pharmacy_collection(self):
        medicine = SimpleNamespace(update=AsyncMock())
        updated = SimpleNamespace(nombre="Nombre actualizado")

        with (
            patch.object(
                MedicamentoFarmacia,
                "get",
                new=AsyncMock(side_effect=[medicine, updated]),
            ) as pharmacy_get,
            patch.object(Medicamento, "get", new=AsyncMock()) as base_get,
        ):
            result = await update_medicamento_farmacia(
                VALID_ID,
                MedicamentoUpdate(nombre="  Nombre actualizado  "),
            )

        medicine.update.assert_awaited_once_with(
            {"$set": {"nombre": "Nombre actualizado"}}
        )
        self.assertEqual(pharmacy_get.await_count, 2)
        base_get.assert_not_awaited()
        self.assertIs(result, updated)

    async def test_rejects_empty_name(self):
        medicine = SimpleNamespace(update=AsyncMock())
        with patch.object(
            MedicamentoFarmacia, "get", new=AsyncMock(return_value=medicine)
        ):
            with self.assertRaises(HTTPException) as error:
                await update_medicamento_farmacia(
                    VALID_ID,
                    MedicamentoUpdate(nombre="   "),
                )

        self.assertEqual(error.exception.status_code, 422)
        medicine.update.assert_not_awaited()

    async def test_reports_duplicate_barcode(self):
        medicine = SimpleNamespace(
            update=AsyncMock(side_effect=DuplicateKeyError("duplicate"))
        )
        with patch.object(
            MedicamentoFarmacia, "get", new=AsyncMock(return_value=medicine)
        ):
            with self.assertRaises(HTTPException) as error:
                await update_medicamento_farmacia(
                    VALID_ID,
                    MedicamentoUpdate(codigo_barra="123"),
                )

        self.assertEqual(error.exception.status_code, 409)

    async def test_rejects_invalid_id_without_querying_database(self):
        with patch.object(
            MedicamentoFarmacia, "get", new=AsyncMock()
        ) as pharmacy_get:
            with self.assertRaises(HTTPException) as error:
                await update_medicamento_farmacia(
                    "id-invalido",
                    MedicamentoUpdate(nombre="Nombre"),
                )

        self.assertEqual(error.exception.status_code, 400)
        pharmacy_get.assert_not_awaited()


class ExportMedicamentosFarmaciaTests(unittest.IsolatedAsyncioTestCase):
    async def test_exports_all_fields_only_from_pharmacy_collection(self):
        medicine = SimpleNamespace(
            model_dump=lambda **kwargs: {
                "id": VALID_ID,
                "codigo_barra": "123456",
                "rs": "RS-1",
                "nombre": "Analg\u00e9sico",
                "forma_farmaceutica": "Tableta",
                "laboratorio": "Laboratorio Uno",
                "distribuidor": "Distribuidor Uno",
                "principio_activo": "Principio",
                "enlace": "https://example.com",
                "accion_terapeutica": "Acci\u00f3n",
                "categoria": "DOLOR",
                "formulacion": "F\u00f3rmula",
                "presentaciones": "Caja",
                "descripcion": 'Descripci\u00f3n con coma, salto\nde l\u00ednea y "comillas"',
            }
        )
        query = SimpleNamespace()
        query.sort = Mock(return_value=query)
        query.to_list = AsyncMock(return_value=[medicine])

        with (
            patch.object(MedicamentoFarmacia, "find_all", return_value=query),
            patch.object(Medicamento, "find_all") as base_find_all,
        ):
            response = await exportar_medicamentos_farmacia_csv()

        base_find_all.assert_not_called()
        self.assertEqual(response.media_type, "text/csv; charset=utf-8")
        self.assertIn(
            "medicamentos_farmacia.csv",
            response.headers["content-disposition"],
        )

        text = response.body.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["nombre"], "Analg\u00e9sico")
        self.assertEqual(
            rows[0]["descripcion"],
            'Descripci\u00f3n con coma, salto de l\u00ednea y "comillas"',
        )
        self.assertEqual(rows[0]["id"], VALID_ID)
        self.assertNotIn("\n", rows[0]["descripcion"])
        query.sort.assert_called_once_with("_id")


class ExportMedicamentosPrincipalesTests(unittest.IsolatedAsyncioTestCase):
    async def test_exports_only_main_collection_in_creation_order(self):
        medicine = SimpleNamespace(
            model_dump=lambda **kwargs: {
                "id": VALID_ID,
                "nombre": "Medicamento principal",
                "descripcion": "Primera l\u00ednea\nSegunda l\u00ednea, con coma",
            }
        )
        query = SimpleNamespace()
        query.sort = Mock(return_value=query)
        query.to_list = AsyncMock(return_value=[medicine])

        with (
            patch.object(Medicamento, "find_all", return_value=query),
            patch.object(MedicamentoFarmacia, "find_all") as pharmacy_find_all,
        ):
            response = await exportar_medicamentos_csv()

        pharmacy_find_all.assert_not_called()
        query.sort.assert_called_once_with("_id")
        self.assertIn("medicamentos.csv", response.headers["content-disposition"])

        rows = list(
            csv.DictReader(io.StringIO(response.body.decode("utf-8-sig")))
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["nombre"], "Medicamento principal")
        self.assertEqual(
            rows[0]["descripcion"],
            "Primera l\u00ednea Segunda l\u00ednea, con coma",
        )


if __name__ == "__main__":
    unittest.main()
