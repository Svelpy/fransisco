import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from main import update_medicamento_farmacia
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


if __name__ == "__main__":
    unittest.main()
