import csv
import os
import re
from recipe_scrapers import scrape_me
from recipeconverter import utils


def import_conversions(filename) -> list:
    """Import ingredient conversion table

    Returns:
        list: List of dicts (ingredient, cup, tablespoon, teaspoon)
    """
    with open(filename) as csvfile:
        conversion_table = list(csv.reader(csvfile, delimiter=","))

    # Remove header
    header = conversion_table[0]
    conversion_table.pop(0)

    # Convert list of lists to list of dicts
    out_table = []
    for line in conversion_table:
        d = {
            header[0]: line[0],
            header[1]: utils.string_to_float(line[1]),
            header[2]: utils.string_to_float(line[2]),
            header[3]: utils.string_to_float(line[3]),
        }
        out_table.append(d)

    return out_table


class RecipeConverter:
    """Convert ingredients and recipes from volumetric to mass units. Includes
    commonly used baking ingredients such as flour, sugar, etc.
    """

    OUNCE_TO_GRAM = 28.3495
    POUND_TO_GRAM = 453.592

    def __init__(self):
        # Values from https://www.cooksillustrated.com/how_tos/5490-baking-conversion-chart
        database_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "gram-conversions.csv"
        )
        self._conversion_table = import_conversions(database_path)

    def convert_recipe_from_url(self, url: str, multiplier=1.0) -> tuple:
        """Convert recipe from URL, if supported"""
        scraper = scrape_me(url)
        ingredients = "\n".join(scraper.ingredients())
        return self.convert_recipe(ingredients, multiplier), scraper

    def convert_recipe(self, recipe: str, multiplier=1.0) -> str:
        """Convert a multi-line recipe from volumetric units to mass units"""
        output = ""
        for line in recipe.split("\n"):
            try:
                output += self.convert_volume_to_mass(line, multiplier) + "\n"
            except Exception as e:
                print(f"Could not convert: '{line}'")
                print(repr(e))
                output += line + "\n"
        return output.strip()

    def convert_volume_to_mass(self, line: str, multiplier=1.0) -> str:
        """Convert ingredient line from volume to mass (grams)"""
        amount, unit, ingredient = self.extract_from_line(line.lower())

        if not all([amount, ingredient]):
            raise ValueError(f"Could not parse line: '{line}'")

        amount = utils.fraction_to_float(amount)

        if unit == "ounce":
            conversion = self.OUNCE_TO_GRAM
            unit = "g"
        elif unit == "pound":
            conversion = self.POUND_TO_GRAM
            unit = "g"
        else:
            conversion, unit = self.get_ingredient_conversion(ingredient, unit)

        amount_converted = amount * conversion * multiplier

        if amount_converted.is_integer():
            amount_converted = int(amount_converted)
        else:
            amount_converted = round(amount_converted, 1)

        unit_out = f" {unit} " if unit else " "
        return f"{amount_converted}{unit_out}{ingredient}"

    def get_ingredient_conversion(self, ingredient: str, unit: str) -> float:
        """Get conversion factor for the given ingredient and unit"""
        ingredient_found = False

        for conversion_line in self._conversion_table:
            if conversion_line["ingredient"] in ingredient:
                conversion = conversion_line[unit]
                ingredient_found = True
                break

        if not ingredient_found:
            conversion = 1
            unit_out = unit
        else:
            unit_out = "g"

        return conversion, unit_out

    @staticmethod
    def extract_from_line(line: str) -> tuple:
        """Extract amount, unit, and ingredient from a recipe line"""
        compatible_units = ["cup", "tablespoon", "teaspoon", "ounce", "pound"]
        regex_compatible = r"(.+?)(cup|tablespoon|teaspoon|ounce|pound)(?:s|)(.*)"
        regex_incompatible = r"(.+?)(?=[a-zA-Z])(.*)"

        # Normalize unit names
        line = line.replace("tbsp", "tablespoon")
        line = line.replace("tsp", "teaspoon")
        line = line.replace("oz", "ounce")
        line = line.replace("lbs", "pound")
        line = line.replace("lb", "pound")

        try:
            if any(x in line for x in compatible_units):
                m = re.findall(regex_compatible, line)
                if not m:
                    raise ValueError("No compatible unit match found.")
                amount = m[0][0].strip()
                unit = m[0][1].strip()
                ingredient = m[0][2].strip()
            else:
                m = re.findall(regex_incompatible, line)
                if not m:
                    raise ValueError("No fallback match found.")
                amount = m[0][0].strip()
                unit = ""
                ingredient = m[0][1].strip()

            return amount, unit, ingredient

        except Exception as e:
            print(f"[extract_from_line ERROR] Line: '{line}' | {repr(e)}")
            return None, None, None
