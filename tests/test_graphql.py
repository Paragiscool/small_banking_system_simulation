import pytest

def test_graphql_query(client, auth_headers):
    query = """
    query {
        accounts {
            accountId
            currency
            balance {
                availableBalance
            }
        }
    }
    """
    
    response = client.post("/graphql", json={"query": query}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "accounts" in data["data"]
    assert len(data["data"]["accounts"]) >= 0

def test_graphql_unauthorized(client):
    query = """
    query {
        accounts {
            accountId
        }
    }
    """
    
    # Missing auth headers
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert "Not authenticated" in data["errors"][0]["message"]
