import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import (
    load_food_data, initialize_model, calculate_calorie_needs,
    generate_meal_plan, get_macros_by_bmi, generate_meal, adjust_calories_by_goal
)

@pytest.fixture
def mock_food_df():
    return pd.DataFrame({
        "Food Name": ["Chicken", "Rice", "Broccoli", "Beef", "Oats"],
        "Calories (kcal)": [165, 130, 55, 250, 389],
        "Protein (g)": [31, 2.5, 3.7, 26, 17],
        "Carbohydrates (g)": [0, 28, 11, 0, 66],
        "Fats (g)": [3.6, 0.3, 0.6, 20, 7]
    })

def test_load_food_data_success(tmp_path, mock_food_df):
    file_path = tmp_path / "food_database.xlsx"
    mock_food_df.to_excel(file_path, index=False, engine="openpyxl")

    with patch("app.os.getcwd", return_value=str(tmp_path)):
        food_dict = load_food_data()
        assert isinstance(food_dict, dict)
        assert "Chicken" in food_dict

        chicken_data = food_dict["Chicken"]
        assert isinstance(chicken_data, dict)
        assert "Calories (kcal)" in chicken_data
        assert "Protein (g)" in chicken_data
        assert "Carbohydrates (g)" in chicken_data
        assert "Fats (g)" in chicken_data
        assert chicken_data["Calories (kcal)"] == 165
        assert chicken_data["Protein (g)"] == 31.0

def test_initialize_model(mock_food_df):
    mock_food_dict = mock_food_df.set_index("Food Name")[["Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fats (g)"]].to_dict(orient="index")
    with patch("app.food_database", mock_food_dict):
        model, df = initialize_model()
        assert model is not None
        assert not df.empty
        assert "protein" in df.columns

def test_calculate_calorie_needs():
    assert calculate_calorie_needs(22, 70, 'sedentary') == pytest.approx(70 * 22 * 1.2)
    assert calculate_calorie_needs(17, 60, 'active') > calculate_calorie_needs(22, 60, 'active')
    assert calculate_calorie_needs(28, 80, 'moderate') < calculate_calorie_needs(22, 80, 'moderate')

def test_get_macros_by_bmi():
    assert get_macros_by_bmi(17)['protein'] == 0.25
    assert get_macros_by_bmi(30)['protein'] == 0.35
    assert get_macros_by_bmi(22)['carbs'] == 0.45

def test_adjust_calories_by_goal():
    assert adjust_calories_by_goal(2000, 'gain_weight', 18) == 2200
    assert adjust_calories_by_goal(2000, 'lose_weight', 27) == 1800
    assert adjust_calories_by_goal(2000, 'maintain', 22) == 2000

def test_generate_meal(monkeypatch, mock_food_df):
    mock_dict = mock_food_df.set_index("Food Name")[["Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fats (g)"]].to_dict(orient="index")
    with patch("app.food_database", mock_dict):
        model, df = initialize_model()

        monkeypatch.setattr("app.food_model", model)
        monkeypatch.setattr("app.food_df", df)

        macros = {'protein': 0.3, 'carbs': 0.5, 'fat': 0.2}
        meal = generate_meal(600, macros)
        assert isinstance(meal, dict)
        assert 'foods' in meal
        assert len(meal['foods']) > 0
        assert 'name' in meal['foods'][0]

def test_generate_meal_plan(monkeypatch, mock_food_df):
    mock_dict = mock_food_df.set_index("Food Name")[["Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fats (g)"]].to_dict(orient="index")
    with patch("app.food_database", mock_dict):
        model, df = initialize_model()

        monkeypatch.setattr("app.food_model", model)
        monkeypatch.setattr("app.food_df", df)

        bmi = 22
        total_calories = 2200
        plan = generate_meal_plan(bmi, total_calories)

        assert 'breakfast' in plan
        assert 'lunch' in plan
        assert 'snacks' in plan
        assert isinstance(plan['snacks'], list)
        assert 'total_calories' in plan
