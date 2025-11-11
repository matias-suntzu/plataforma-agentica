from tools.campaigns import buscar_id_campana_func
from models.schemas import BuscarIdCampanaInput

def test_buscar_ibiza():
    input = BuscarIdCampanaInput(nombre_campana="ibiza")
    result = buscar_id_campana_func(input)
    assert result.id_campana != "None"