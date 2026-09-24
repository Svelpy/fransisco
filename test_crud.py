import os
os.environ["MONGODB_DB_NAME"] = "test_medicamentos_db"

from fastapi.testclient import TestClient
from main import app

def test_crud():
    print("Starting tests...")
    with TestClient(app) as client:
        # Create
        print("Testing CREATE...")
        create_data = {
            "nombre": "Paracetamol 500mg",
            "codigo_barra": "1234567890123",
            "laboratorio": "Lab Genérico",
            "principio_activo": "Paracetamol"
        }
        resp = client.post("/medicamentos", json=create_data)
        assert resp.status_code == 201, f"Failed to create: {resp.text}"
        created = resp.json()
        print(f"Created successfully: {created}")
        med_id = created["id"]
        
        # Read
        print("\nTesting GET by ID...")
        resp = client.get(f"/medicamentos/{med_id}")
        assert resp.status_code == 200, f"Failed to get: {resp.text}"
        print(f"Got successfully: {resp.json()}")
        
        # Update
        print("\nTesting UPDATE...")
        update_data = {
            "nombre": "Paracetamol 500mg (Actualizado)",
            "laboratorio": "Lab Genérico 2"
        }
        resp = client.put(f"/medicamentos/{med_id}", json=update_data)
        assert resp.status_code == 200, f"Failed to update: {resp.text}"
        print(f"Updated successfully: {resp.json()}")
        
        # List (Pagination and Search)
        print("\nTesting LIST / SEARCH...")
        resp = client.get("/medicamentos?q=paracetamol")
        assert resp.status_code == 200, f"Failed to list: {resp.text}"
        data = resp.json()
        print(f"List response total: {data['total']}, items: {len(data['data'])}")
        
        # Delete
        print("\nTesting DELETE...")
        resp = client.delete(f"/medicamentos/{med_id}")
        assert resp.status_code == 204, f"Failed to delete: {resp.text}"
        print("Deleted successfully")
        
        # Confirm Delete
        print("\nConfirming DELETE...")
        resp = client.get(f"/medicamentos/{med_id}")
        assert resp.status_code == 404, f"Should be 404 but got {resp.status_code}: {resp.text}"
        print("Confirmed deletion (404 received as expected).")
        
        print("\nAll CRUD operations tested successfully!")

if __name__ == "__main__":
    try:
        test_crud()
    except Exception as e:
        import traceback
        traceback.print_exc()
