import csv
import math
from collections import defaultdict
from io import StringIO
from typing import Optional

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse

from apps.constants import LOGGER
from apps.mixin import ViewMixin
from apps.proposal.product.models import AdditionalMaterials, Product

from ..models import (
    GlueAndAdditionalMaterial,
    MaterialList,
    Opportunity,
    PreliminaryMaterialList,
)


class UploadCADFile(ViewMixin):
    """View for handling the upload of CAD files and processing material lists."""

    def generate_material_list(self, uploaded_file: InMemoryUploadedFile, document_number: str) -> dict:
        """
        Generates material list from an uploaded file.

        :param uploaded_file: Uploaded file object (InMemoryUploadedFile).
        :param document_number: Document number for the associated opportunity.
        :return: Dictionary containing the material list data.
        """
        material_list_obj = MaterialList.objects.filter(opportunity__document_number=document_number)

        if len(material_list_obj) != 0:
            MaterialList.objects.filter(opportunity__document_number=document_number).delete()
            GlueAndAdditionalMaterial.objects.filter(opportunity__document_number=document_number).delete()
            PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number).delete()

        data = {"Quantity": [], "Description": [], "Item Number": []}

        # Get the opportunity instance to save the material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            LOGGER.error(f"Opportunity with document number {document_number} not found.")
            return data

        # Read the file content
        file_content = uploaded_file.read().decode("utf-8")
        file_like_object = StringIO(file_content)

        reader = csv.reader(file_like_object)
        for row in reader:
            if len(row) != 3:
                continue

            quantity, description, item_number = row

            # Append the values to the corresponding lists in the dictionary
            data["Quantity"].append(float(quantity))
            data["Description"].append(description)
            data["Item Number"].append(item_number)

            # Save data into the database
            MaterialList.objects.create(
                opportunity=opportunity, quantity=float(quantity), description=description, item_number=item_number
            )
        return data

    def apply_transformations(self, row: pd.Series) -> pd.Series:
        """Helper function to generate rows with calculations for Material List."""
        description = row["Description"]

        # Formula for form1
        form1 = description.replace('"', "")

        # Formula for form2
        if '"' in description:
            quote_index = description.find('"')
            form2 = description[:3] + description[quote_index - 2 : quote_index]
        else:
            form2 = description[:3]  # fallback if no quote found

        # Formula for form3
        if '"' in description:
            quote_index = description.find('"')
            form3 = description[quote_index - 5 : quote_index].replace("  ", " ")
        else:
            form3 = description  # fallback if no quote found

        # Formula for form4
        if " " in form3:
            space_index = form3.find(" ")
            form4 = description[:3] + " " + form3[space_index + 1 : space_index + 11].strip()
        else:
            form4 = description[:3]  # fallback if no space found in form3

        return pd.Series([form1, form2, form3, form4], index=["form1", "form2", "form3", "form4"])

    def calculate_additional_columns(self, row: pd.Series) -> pd.Series:
        """Helper function to generate rows with calculations for Material List."""

        description = row["Description"]
        form1 = row["form1"]
        form3 = row["form3"]

        # Extract 'Tee's'
        if "TEE" in description:
            if "X " in description:
                start_index = description.find("X ") + 2
                tee_value = description[start_index : start_index + 4].strip()
            else:
                tee_value = description.split(" ")[-1].strip()
        else:
            tee_value = "ERR"

        # Extract 'RED BUSH & COUPS'
        if "RED BUSH" in description:
            red_bush_value = description.split("X ")[-1].split("SPXS")[0].strip()
        elif "RED COUP" in description:
            red_bush_value = description.split("X ")[-1].strip()
        else:
            red_bush_value = "IFERR"

        # Extract 'CROSS'
        if "CROSS" in form1:
            if "X " in form1:
                start_index = form1.find("X ") + 2
                cross_value = form1[start_index : start_index + 4].strip()
            else:
                if " " in form3:
                    space_index = form3.find(" ")
                    cross_value = form3[space_index + 1 : space_index + 4].strip()
                else:
                    cross_value = "ERR"
        else:
            cross_value = "ERR"

        # Extract 'Hose'
        hose_value = description[:14].strip()

        return pd.Series(
            [tee_value, red_bush_value, cross_value, hose_value], index=["Tee's", "RED BUSH & COUPS", "CROSS", "Hose"]
        )

    def calculate_mains_manifold(self, df: pd.DataFrame, pipe_size: float, joints_per_pint: float) -> dict:
        """Helper function to generate rows with calculations for Glue & Additional Material List."""

        # Filters based on pipe size and type
        solvent_weld_pipe = df[
            df["form1"].str.contains(f"PIPE.*{pipe_size} SW", case=False, na=False)
            | df["form1"].str.contains(f"PIPE.*{pipe_size} BE", case=False, na=False)
        ]

        # Cross joints calculation using the formula provided
        cross_joints_from_form4 = df[df["form4"].str.contains(f"CRO {pipe_size}", case=False, na=False)][
            "Quantity"
        ].sum()
        cross_joints_from_cross = df[df["CROSS"].str.contains(f"{pipe_size}", case=False, na=False)]["Quantity"].sum()
        cross_joints_sum = (cross_joints_from_form4 + cross_joints_from_cross) * 2

        # Tee joints calculation
        tee_joints_formula = (
            df[df["form4"].str.contains(f"TEE {pipe_size}", case=False, na=False)]["Quantity"].sum() * 2
        ) + df[df["Tee's"].str.contains(f"{pipe_size}", case=False, na=False)]["Quantity"].sum()

        # Elbow, Coupler, RB, RC Joints calculation
        elbow_coupler_rb_rc_joints = (
            df[df["form4"].str.contains(f"ELB {pipe_size}", case=False, na=False)]["Quantity"].sum() * 2
            + df[df["form4"].str.contains(f"COU {pipe_size}", case=False, na=False)]["Quantity"].sum() * 2
            + df[df["form4"].str.contains(f"RED {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"FLA {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"CAP {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"FA {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"MA {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["RED BUSH & COUPS"].str.contains(f"{pipe_size}", case=False, na=False)]["Quantity"].sum()
        )

        # Sum quantities
        solvent_weld_pipe_sum = solvent_weld_pipe["Quantity"].sum()
        cross_joints_sum = cross_joints_sum
        tee_joints_sum = tee_joints_formula
        elbow_coupler_rb_rc_joints_sum = elbow_coupler_rb_rc_joints
        total_joints = (solvent_weld_pipe_sum / 20) + cross_joints_sum + tee_joints_sum + elbow_coupler_rb_rc_joints_sum
        pints = total_joints / joints_per_pint
        thrust_block_conc_bags = 0

        return {
            "Pipe Size": pipe_size,
            "Solvent Weld Pipe": solvent_weld_pipe_sum,
            "Cross Joints": cross_joints_sum,
            "Tee Joints": tee_joints_sum,
            "Elbow, Coupler, RB, RC Joints": elbow_coupler_rb_rc_joints_sum,
            "TOTAL JOINTS": total_joints,
            "JOINTS PER PINT": joints_per_pint,
            "PINTS": round(pints, 1),
            "Thrust Block # Conc. Bags": thrust_block_conc_bags,
        }

    def calculate_flex_riser_quantities(self, df: pd.DataFrame, values: list) -> pd.DataFrame:
        """Helper function to generate rows with calculations for Glue & Additional Material List."""

        results = []

        # Calculate the quantity for '1/2' Flex Risers (C37) and '1/2' Saddles (D37)
        flex_riser_half_data = df[df["form1"].str.contains("FLEX RISER", case=False, na=False)]
        flex_riser_half_sum = flex_riser_half_data.groupby("form1")["Quantity"].sum().reset_index()
        flex_riser_half_sum = flex_riser_half_sum[
            flex_riser_half_sum["form1"].str.contains("1/2", case=False, na=False)
        ]
        C37 = flex_riser_half_sum["Quantity"].sum()

        saddle_half_data = df[df["form1"].str.contains("SADDLE", case=False, na=False)]
        saddle_half_sum = saddle_half_data.groupby("form1")["Quantity"].sum().reset_index()
        saddle_half_sum = saddle_half_sum[saddle_half_sum["form1"].str.contains("1/2", case=False, na=False)]
        D37 = saddle_half_sum["Quantity"].sum()

        for value in values:
            # Filter for Flex Risers
            flex_riser_data = df[df["form1"].str.contains("FLEX RISER", case=False, na=False)]

            # Aggregate quantities for Flex Risers
            flex_riser_sum = flex_riser_data.groupby("form1")["Quantity"].sum().reset_index()
            flex_riser_sum = flex_riser_sum[flex_riser_sum["form1"].str.contains(f"{value}", case=False, na=False)]
            flex_riser_total = flex_riser_sum["Quantity"].sum()

            # Special handling for value == '1'
            if value == "1":
                if flex_riser_total == 0:
                    flex_riser_total = 0
                else:
                    flex_riser_total = flex_riser_total - C37

            # Filter for Saddles
            saddle_data = df[df["form1"].str.contains("SADDLE", case=False, na=False)]

            # Aggregate quantities for Saddles
            saddle_sum = saddle_data.groupby("form1")["Quantity"].sum().reset_index()
            saddle_sum = saddle_sum[saddle_sum["form1"].str.contains(f"{value}", case=False, na=False)]
            saddle_total = saddle_sum["Quantity"].sum()

            # Special handling for value == '1'
            if value == "1":
                if saddle_total == 0:
                    saddle_total = 0
                else:
                    saddle_total = saddle_total - D37

            # Calculate Total Joints
            total_joints = flex_riser_total + saddle_total

            # Define Joints per Pint
            if value == "1":
                joints_per_pint = 25
            elif value == "1/2":
                joints_per_pint = 50
            elif value == "3/4":
                joints_per_pint = 50
            else:
                joints_per_pint = 0

            # Calculate Pints
            pints = total_joints / joints_per_pint

            # Append result for current value
            results.append(
                {
                    "Size": value,
                    "Flex Risers": flex_riser_total,
                    "Saddles": saddle_total,
                    "Total Joints": total_joints,
                    "JOINTS PER PINT": joints_per_pint,
                    "Pints": round(pints, 1),
                }
            )

        # Create DataFrame for Flex Risers and Saddles
        flex_riser_summary = pd.DataFrame(results)

        return flex_riser_summary

    def __custom_round(self, value: float) -> float:
        """Round the given total to the nearest whole number (upward)."""
        return math.ceil(value)

    def __custom_sum(self, *args) -> float:
        """
        Sum the given numbers.

        NOTE: Currently, we are not using this function.
        """
        return sum(args)

    def __evaluate_formula(self, qty: str, amf: str, formula: str) -> Optional[float]:
        """
        Evaluate the given formula string after substituting 'qty' and 'amf'.

        NOTE: Fetch `amf` and `qty` value after `Material List` generated.
        TODO: Fetch `qty``from CAD file Data and `amf` from Table `Glue and Additional Materials Master Table` filed Additional Material Factor
        """
        formula = formula.replace("$qty", str(qty)).replace("$amf", str(amf))
        formula_content = formula.replace("(", "").replace(")", "").replace("round", "").strip()

        if formula_content.startswith("sum"):
            values = formula_content.replace("sum", "").strip()
            args = [float(num.strip()) for num in values.split(",")]
            total_value = self.__custom_round(*args)
            return self.__custom_round(total_value)

        elif formula_content.startswith("round"):
            try:
                result = eval(formula_content)
                print(f"result {type(result)}: {result}")
                return self.__custom_round(result)

            except Exception as e:
                print(f"Error evaluating formula '{formula_content}': {e}")
                return None

        else:
            formula = formula.replace("$qty", str(qty)).replace("$amf", str(amf))
            value = eval(formula)
            return round(value, 2)

    def get_final_unit(self, qty: str, item_number: str) -> Optional[float]:
        """Get final unit based on a single formula."""
        try:
            _amf = AdditionalMaterials.objects.get(product_item_number=item_number)
            _formula = Product.objects.get(internal_id=_amf.material_id)
            return self.__evaluate_formula(qty, _amf.additional_material_factor, _formula.formula)
        except AdditionalMaterials.DoesNotExist:
            LOGGER.error(f"AdditionalMaterials Not Exist")

    def generate_glue_and_additional_material_list(self, material_list: dict, document_number: str) -> dict:
        """
        Generate Glu and Additional Material List.

        :param document_number: Document number for the associated opportunity.
        """
        glue_and_additional_data = {"Quantity": [], "Description": [], "Item": []}

        for qty, item in zip(material_list["Quantity"], material_list["Item Number"]):
            # print(f"Quantity: {qty}, Item Number: {item.strip()}")
            glue_qty = self.get_final_unit(qty, item)
            
            if glue_qty:
                material = AdditionalMaterials.objects.get(product_item_number=item)
                glue_and_additional_data["Quantity"].append(glue_qty)
                glue_and_additional_data["Description"].append(material.material_name)
                glue_and_additional_data["Item"].append(item.strip())

        # Get the opportunity instance to save the Glue and Additional material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            LOGGER.error(f"Opportunity with document number {document_number} not found.")
            return glue_and_additional_data

        for i in range(len(glue_and_additional_data["Item"])):
            GlueAndAdditionalMaterial.objects.create(
                opportunity=opportunity,
                quantity=glue_and_additional_data["Quantity"][i],
                description=glue_and_additional_data["Description"][i],
                item_number=glue_and_additional_data["Item"][i],
            )

        return glue_and_additional_data

    def add_to_merged_data(self, data: dict, key_field: str, merged_data: defaultdict):
        """Helper function to generate rows with calculations for Glue & Additional Material List."""

        for quantity, description, item_number in zip(data["Quantity"], data["Description"], data[key_field]):
            if item_number in merged_data:
                # Append quantity if item number already exists
                merged_data[item_number]["Quantity"].append(quantity)
            else:
                # Create a new entry
                merged_data[item_number]["Description"] = description
                merged_data[item_number]["Item Number"] = item_number
                merged_data[item_number]["Quantity"] = [quantity]

    def generate_preliminary_material_list(
        self, material_list: dict, glue_and_additional_data: dict, document_number: str
    ) -> dict:
        """
        Generate and save preliminary material list into the database.

        :param material_list : Material List data.
        :param glue_and_additional_data : Glue & Additional Material List data.
        :param document_number: Document number for the associated opportunity.
        """
        # Get the opportunity instance to save the Glue and Additional material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            LOGGER.error(f"Opportunity with document number {document_number} not found.")
            return glue_and_additional_data

        # Initialize data structures
        irricad_data = material_list
        glue_data = glue_and_additional_data

        # Create dictionaries for mapping item numbers to quantities
        irricad_quantities = {
            item.strip(): quantity for item, quantity in zip(irricad_data["Item Number"], irricad_data["Quantity"])
        }
        glue_quantities = {item.strip(): quantity for item, quantity in zip(glue_data["Item"], glue_data["Quantity"])}

        # Combine quantities for the same item_number
        combined_quantities = defaultdict(
            lambda: {"Irricad Imported Quantities": 0, "Glue & Additional Mat'l Quantities": 0}
        )

        # Add quantities from Irricad data
        for item_number, quantity in irricad_quantities.items():
            combined_quantities[item_number]["Irricad Imported Quantities"] += quantity

        # Add quantities from Glue & Additional Material data
        for item_number, quantity in glue_quantities.items():
            combined_quantities[item_number]["Glue & Additional Mat'l Quantities"] += quantity

        # Calculate Combined Quantities from both imports
        for item_number in combined_quantities:
            combined_quantities[item_number]["Combined Quantities from both Imports"] = (
                combined_quantities[item_number]["Irricad Imported Quantities"]
                + combined_quantities[item_number]["Glue & Additional Mat'l Quantities"]
            )

        # Map descriptions from both data sources
        description_dict = {}
        # Add descriptions from glue_data
        for item, description in zip(glue_data["Item"], glue_data["Description"]):
            description_dict[item] = description

        # Add descriptions from irricad_data if not already present
        for item, description in zip(
            irricad_data["Item Number"], irricad_data["Description"] * len(irricad_data["Item Number"])
        ):
            if item not in description_dict:
                description_dict[item] = description

        # Prepare final data for output
        final_data = {
            "Irricad Imported Quantities": [],
            "Glue & Additional Mat'l Quantities": [],
            "Combined Quantities from both Imports": [],
            "Description": [],
            "Item Number": [],
        }

        # Fill final data with combined values
        for item_number, values in combined_quantities.items():
            final_data["Item Number"].append(item_number)
            final_data["Description"].append(description_dict.get(item_number, "Description not available"))
            final_data["Irricad Imported Quantities"].append(values["Irricad Imported Quantities"])
            final_data["Glue & Additional Mat'l Quantities"].append(values["Glue & Additional Mat'l Quantities"])
            final_data["Combined Quantities from both Imports"].append(values["Combined Quantities from both Imports"])

        # Save each unique combination to the database
        for item_number, values in combined_quantities.items():
            PreliminaryMaterialList.objects.create(
                opportunity=opportunity,
                irricad_imported_quantities=values["Irricad Imported Quantities"],
                glue_and_additional_mat_quantities=values["Glue & Additional Mat'l Quantities"],
                combined_quantities_from_both_import=values["Combined Quantities from both Imports"],
                description=description_dict.get(item_number, "Description not available"),
                item_number=item_number,
                # Add any additional fields if necessary
            )

        return final_data

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handel POST request for uploaded CAD File.
        """
        if "file" not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        uploaded_file = request.FILES["file"]
        document_number = request.POST.get("document_number")

        if uploaded_file.name.lower().endswith(".tmp"):
            # Generate and save Material List
            # NOTE: Converted Macro code into python ("Split List")
            material_list = self.generate_material_list(uploaded_file, document_number)
            material_list_df = pd.DataFrame(material_list)

            # Helper function to calculate ['form1', 'form2', 'form3', 'form4'] for material list
            material_list_df[["form1", "form2", "form3", "form4"]] = material_list_df.apply(
                self.apply_transformations, axis=1
            )

            # Helper function to calculate ['Tee\'s', 'RED BUSH & COUPS', 'CROSS', 'Hose'] for material list
            material_list_df[["Tee's", "RED BUSH & COUPS", "CROSS", "Hose"]] = material_list_df.apply(
                self.calculate_additional_columns, axis=1
            )

            # Define pipe sizes and joints per pint
            pipe_sizes = [24, 21, 20, 18.7, 15, 12, 10, 8, 6, 5, 4, 3, 2.5, 2]
            joints_per_pint_values = {
                24: 0.0625,
                21: 0.125,
                20: 0.125,
                18.7: 0.25,
                15: 0.375,
                12: 0.5,
                10: 1,
                8: 2,
                6: 5,
                5: 10,
                4: 15,
                3: 20,
                2.5: 25,
                2: 30,
            }

            # Calculate values for each pipe size
            mains_manifold_results = []
            for pipe_size in pipe_sizes:
                joints_per_pint = joints_per_pint_values.get(pipe_size, "")
                mains_manifold_data = self.calculate_mains_manifold(material_list_df, pipe_size, joints_per_pint)
                mains_manifold_results.append(mains_manifold_data)

            # Create a DataFrame for mains and manifold pipes
            # mains_manifold_df = pd.DataFrame(mains_manifold_results)

            # Calculate Flex Riser Quantities
            values = ["1/2", "3/4", "1"]
            # flex_riser_df = self.calculate_flex_riser_quantities(material_list_df, values)
            self.calculate_flex_riser_quantities(material_list_df, values)

            # Generate and save Glue & Additional Material List
            # NOTE: Converted Macro code into python ("Run Miscellaneous Material")
            # _glue_and_additional_data_df
            glue_and_additional_data = self.generate_glue_and_additional_material_list(material_list, document_number)
            # glue_and_additional_data_df = pd.DataFrame(glue_and_additional_data)

            # Generate and save Preliminary Material List
            # NOTE: Converted Macro code into python ("Import Material from Previous Tabs", "FINALIZE MATERIAL")

            # --[Import Material from Previous Tabs]
            # Dictionary to store merged data
            merged_data = defaultdict(lambda: {"Quantity": [], "Description": None, "Item Number": None})

            # Add both datasets to merged_data
            self.add_to_merged_data(material_list, "Item Number", merged_data)
            self.add_to_merged_data(glue_and_additional_data, "Item", merged_data)

            # Convert quantities to comma-separated strings and finalize the merged data
            final_merged_data = {
                "Quantity": [],
                "Item Number": [],
                "Description": [],
            }

            for item_number, values in merged_data.items():
                final_merged_data["Item Number"].append(values["Item Number"])
                final_merged_data["Description"].append(values["Description"])
                final_merged_data["Quantity"].append(",".join(map(str, values["Quantity"])))

            # import_from_previous_data = pd.DataFrame(final_merged_data)
            # import_from_previous_data_df = import_from_previous_data.sort_values(by='Item Number').reset_index(drop=True)

            # --[FINALIZE MATERIAL]
            # Generate and save preliminary material list data
            # preliminary_material_list = self.generate_preliminary_material_list(material_list, glue_and_additional_data, document_number)
            # preliminary_material_list_df = pd.DataFrame(preliminary_material_list)
            self.generate_preliminary_material_list(material_list, glue_and_additional_data, document_number)

            return JsonResponse(
                {
                    "message": "Generated Material list, Glue & Additional Material List and Preliminary Material List successfully"
                },
                status=200,
            )

        return JsonResponse({"error": "Invalid file format. Only .tmp files are supported."}, status=400)
