import csv
from collections import defaultdict
from io import StringIO

import pandas as pd
from django.http import JsonResponse

from apps.rental.mixin import ViewMixin

from ..models import (
    GlueAndAdditionalMaterial,
    MaterialList,
    Opportunity,
    PreliminaryMaterialList,
)


class UploadCADFile(ViewMixin):
    """View for handling the upload of CAD files and processing material lists."""

    def generate_material_list(self, uploaded_file, document_number):
        """
        Generates material list from an uploaded file.

        :param uploaded_file: Uploaded file object (InMemoryUploadedFile).
        :param document_number: Document number for the associated opportunity.
        :return: Dictionary containing the material list data.
        """
        material_list_obj = MaterialList.objects.filter(opportunity__document_number=document_number)
        # print("Len :::::::::", len(material_list_obj))

        if len(material_list_obj) != 0:
            MaterialList.objects.filter(opportunity__document_number=document_number).delete()
            GlueAndAdditionalMaterial.objects.filter(opportunity__document_number=document_number).delete()
            PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number).delete()

        data = {"Quantity": [], "Description": [], "Item Number": []}

        # Get the opportunity instance to save the material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print(f"Opportunity with document number {document_number} not found.")
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

    def apply_transformations(self, row):
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

    def calculate_additional_columns(self, row):
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

    def calculate_mains_manifold(self, df, pipe_size, joints_per_pint):
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

    def calculate_flex_riser_quantities(self, df, values):
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

    def generate_glue_and_additional_material_list(self, document_number):
        """
        Generate Glue and Additional Material List.

        :param document_number: Document number for the associated opportunity.
        """
        glue_and_additional_data = {
            "Quantity": [1, 2, 1, 2, 2, 7, 7, 14, 4, 2, 25, 2, 11, 25, 11, 11, 22, 36, 12, 3, 1],
            "Form1": [
                ",1",
                ",2",
                ",1",
                ",2",
                ",2",
                ",7",
                ",7",
                ",14",
                ",4",
                ",2",
                ",25",
                ",2",
                ",11",
                ",25",
                ",11",
                ",11",
                ",22",
                ",36",
                ",12",
                ",3",
                ",1",
            ],
            "Form2": [
                ",1",
                ",2",
                ",1",
                ",2",
                ",2",
                ",7",
                ",7",
                ",14",
                ",4",
                ",2",
                ",25",
                ",2",
                ",11",
                ",25",
                ",11",
                ",11",
                ",22",
                ",36",
                ",12",
                ",3",
                ",1",
            ],
            "Description": [
                "Cement -711 Heavy Gray, Gallon",
                "Cement -719 Extra Heavy Gray, Quart",
                "Cement - Primer Purple P70 Gal",
                "CEMENT - RED HOT CLEAR, PINT",
                "CEMENT - RED HOT CLEAR, PINT (HOSE FITTINGS)",
                'Cement - Empty Can, Quart 1.75" Neck',
                'Cement - Empty Can, Pint 1.75" Neck',
                "Cement - Dauber for Quart Can",
                "Cement - Dauber for Pint Can",
                "Cement - Dauber for Pint Can (HOSE FITTINGS)",
                'COUPLER BLACK 1/2"',
                'COUPLER S40 2"',
                "PERMA-LOC X SWIVEL-W TEE 062",
                "PERMA-LOC COUPLING 062",
                'Ball Valve, Riser 3/4" FHTxMHT',
                'MALE HOSE ADAP X 1/2"S(3/4"SP)',
                "FIGURE 8 062",
                'FLEX RISER 1/2" X 48"',
                'SADDLE 1/2" X 2"',
                'CUT PIPE PVC S40 2" x 48"',
                'SURVEY FLAGS GLO ORA 21" WIRE ',
            ],
            "Item": [
                "4200-001600",
                "4200-002500",
                "4200-007500",
                "4200-005000",
                "4200-005000",
                "4200-013000",
                "4200-013500",
                "4200-014500",
                "4200-015000",
                "4200-015000",
                "2800-116500",
                "429020",
                "2800-006000",
                "2800-001000",
                "2800-117500",
                "2800-114000",
                "2800-118500",
                "6200-008000",
                "2800-105000",
                "5400-031120",
                "3600-004500",
            ],
            "Category": [
                "#N/A",
                "GLU010",
                "GLU020",
                "GLU010",
                "FHO",
                "GLU040",
                "GLU040",
                "GLU040",
                "GLU040",
                "FHO",
                "FHO910",
                "FMP429",
                "FHO010",
                "FHO005",
                "FHO915",
                "FHO905",
                "FHO920",
                "TUB030",
                "FHO900",
                "PIP010",
                "FSO020",
            ],
        }

        # Get the opportunity instance to save the Glue and Additional material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print(f"Opportunity with document number {document_number} not found.")
            return glue_and_additional_data

        for i in range(len(glue_and_additional_data["Item"])):
            GlueAndAdditionalMaterial.objects.create(
                opportunity=opportunity,
                quantity=glue_and_additional_data["Quantity"][i],
                description=glue_and_additional_data["Description"][i],
                item_number=glue_and_additional_data["Item"][i],
                category=glue_and_additional_data["Category"][i],
            )

        return glue_and_additional_data

    def add_to_merged_data(self, data, key_field, merged_data):
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

    def generate_preliminary_material_list(self, material_list, glue_and_additional_data, document_number):
        """
        Generate and save preliminary material list into database.

        :param material_list : Material List data.
        :param glue_and_additional_data : Glue & Additional Material List data.
        :param document_number: Document number for the associated opportunity.
        """
        # Get the opportunity instance to save the Glue and Additional material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print(f"Opportunity with document number {document_number} not found.")
            return glue_and_additional_data

        # Initialize data structures
        irricad_data = material_list
        glue_data = glue_and_additional_data

        # Create dictionaries for mapping item numbers to quantities
        irricad_quantities = {
            item: quantity for item, quantity in zip(irricad_data["Item Number"], irricad_data["Quantity"])
        }
        glue_quantities = {item: quantity for item, quantity in zip(glue_data["Item"], glue_data["Quantity"])}

        # Create a dictionary to hold the combined results
        combined_data = defaultdict(lambda: {"Irricad Imported Quantities": 0, "Glue & Additional Mat'l Quantities": 0})
        # Populate combined data with quantities from Irricad
        for item_number, quantity in irricad_quantities.items():
            combined_data[item_number]["Irricad Imported Quantities"] += quantity

        # Populate combined data with quantities from Glue & Additional Mat'l
        for item_number, quantity in glue_quantities.items():
            combined_data[item_number]["Glue & Additional Mat'l Quantities"] += quantity

        # Calculate Combined Quantities from both Imports
        for item_number in combined_data:
            combined_data[item_number]["Combined Quantities from both Imports"] = (
                combined_data[item_number]["Irricad Imported Quantities"]
                + combined_data[item_number]["Glue & Additional Mat'l Quantities"]
            )

        # Map descriptions from both data sources
        description_dict = {}
        # Populate descriptions from glue_data
        for item, description in zip(glue_data["Item"], glue_data["Description"]):
            description_dict[item] = description
        # Add descriptions from irricad_data if not already present
        for item, description in zip(
            irricad_data["Item Number"], irricad_data["Description"] * len(irricad_data["Item Number"])
        ):
            if item not in description_dict:
                description_dict[item] = description

        # Populate the final combined dictionary
        final_data = {
            "Irricad Imported Quantities": [],
            "Glue & Additional Mat'l Quantities": [],
            "Combined Quantities from both Imports": [],
            "Description": [],
            "Item Number": [],
        }

        for item_number, values in combined_data.items():
            final_data["Item Number"].append(item_number)
            final_data["Description"].append(description_dict.get(item_number, "Description not available"))
            final_data["Irricad Imported Quantities"].append(values["Irricad Imported Quantities"])
            final_data["Glue & Additional Mat'l Quantities"].append(values["Glue & Additional Mat'l Quantities"])
            final_data["Combined Quantities from both Imports"].append(values["Combined Quantities from both Imports"])

        # TODO: Need to Create category and bag_bundle_quantity dynamically.
        for item_number, values in combined_data.items():
            PreliminaryMaterialList.objects.create(
                opportunity=opportunity,
                irricad_imported_quantities=values["Irricad Imported Quantities"],
                glue_and_additional_mat_quantities=values["Glue & Additional Mat'l Quantities"],
                combined_quantities_from_both_import=values["Combined Quantities from both Imports"],
                description=description_dict.get(item_number, "Description not available"),
                item_number=item_number,
                category="",
                bag_bundle_quantity="",
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
            # print("Material List Df",material_list_df)

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
            glue_and_additional_data = self.generate_glue_and_additional_material_list(document_number)
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
