
  $(document).ready(function() {

      function generateUniqueId() {
          return "id" + Math.random().toString(16).slice(2);
      }

      // Handle 'Add Row' button click
      $('.add-row-btn').on('click', function() {
          var unique_id = generateUniqueId();
          console.log("unique_id =", unique_id);

          var html = `
          <tr id="row-template-${unique_id}" class="new_prod">
              <td></td>
              <td class="text-nowrap"><input type="text" class="form-control quantity" data-id="quantity-${unique_id}" placeholder="Enter Quantity"></td>
              <td class="text-nowrap">
                  <select data-id="${unique_id}" class="select2-item-code js-example-programmatic form-control">
                  </select>
              </td>
              <td>
                  <select data-id="${unique_id}" class="select2-item-description js-example-programmatic form-control">
                  </select>
              </td>
              <td><input data-id="${unique_id}" id="std_cost" type="text" class="form-control standard-cost" placeholder="Enter Standard Cost"></td>
              <td><input type="text" class="form-control quoted-cost" placeholder="Enter Quoted Cost"></td>
              <td>
                  <select data-id="${unique_id}" class="select2-vendor vendor form-control">
                    <option selected disabled>Select Vendor Name</option>
                  </select>
              </td>
              <td><input type="text" class="form-control comment" placeholder="Enter comment"></td>
              <td><input type="text" class="form-control total" placeholder="Enter Total"></td>
              <td><input type="text" class="form-control sell" placeholder="Enter Sell"></td>
              <td><input type="text" class="form-control sell-total" placeholder="Enter Total"></td>
              <td><input type="text" class="form-control gross" placeholder="Enter Gross %"></td>
              <td><input type="text" class="form-control gross-p" placeholder="Enter Gross %"></td>
              <td class="d-flex">
                  <button type="button" class="btn btn-danger mr-2 remove-row-btn"><i class="fa fa-trash"></i></button>
                  <button type="button" class="btn btn-success mr-2 save"><i class="fa fa-save"></i></button>
              </td>
          </tr>
          `;
          console.log("Clicked..........");
          var data_id = $(this).data('id');
          console.log("data id =", data_id);
          $(`#tableBody-${data_id}`).append(html);

          // Initialize select2 for the new selects
          $('.select2-vendor').select2({
            placeholder: 'Select Vendor Name',
            ajax: {
                url: vendor_url,
                dataType: 'json',
                delay: 250,  // Add a delay for better UX
                data: function (params) {
                    return {
                        q: params.term
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results
                    };
                },
                cache: true
            }
          });

          // Item code start
          $('.select2-item-code').select2({
            placeholder: 'Select Item Code',
            ajax: {
                url: item_code_url,
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        q: params.term
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results
                    };
                },
                cache: true
            }
          });

          function updateDescription(value, id) {
            var $select2Element = $(`select[data-id="${id}"].select2-item-description.js-example-programmatic.form-control`);

            // Initialize Select2
            $select2Element.select2({
                ajax: {
                    url: item_description_url,
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            q: value
                        };
                    },
                    processResults: function(data) {
                        return {
                            results: data.results
                        };
                    },
                    cache: true
                }
            });

            // When Select2 is initialized, set the selected value
            $select2Element.on('select2:open', function() {
                setTimeout(function() {
                    $select2Element.val(value).change();
                }, 100);
            });
          }

          $(document).on('change', '.select2-item-code', function(e) {

            // item code
            var $input = $(e.target);
            var id = $input.data("id");
            console.log("id", id);

            var value = $input.val();
            console.log("value",value);

            // Payload data
            data = {
              value: value,
            }

            $.ajax({
              url: item_code_url,
              type: 'POST',
              data: data,
              headers: {
                'X-CSRFToken': "{{ csrf_token }}",
              },
              success: function(response) {
                console.log('API call success:', response);
                if (response.code == 200) {
                  console.log("description", response.description);
                  console.log("std_cost", response.std_cost, id);
                  updateDescription(response.description, id);
                  var $stdCostField = $(`input[data-id="${id}" id="std_cost"]`);
                  $stdCostField.val(response.std_cost);
                }
              },
              error: function(xhr, status, error) {
                console.log("Error:", error);
              }
            });
          });
          // Item code end

          $(`.select2-item-description`).select2({
            placeholder: 'Select Item description',
            ajax: {
                url: item_description_url,
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        q: params.term
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results
                    };
                },
                cache: true
            }
          });

      });

      $(document).on('click', '.remove-row-btn', function() {
          $(this).closest('tr').remove();
      });

      $(document).on('input', '.quantity', function(){
          var quantity_id = $(this).data('id');
          console.log("quantity_id", quantity_id);
          var quantity_value = $(this).val();
          console.log("quantity_value", quantity_value);
      });

      $(document).on('click', '.save', function(){

        // Get the closest <tr> element to the clicked save button
        var $row = $(this).closest('tr');

        // Extract data from the row
        var quantity = $row.find('.quantity').val();
        var item_code = $row.find('.select2-item-code').val();
        var description = $row.find('.select2-item-description').val();
        var vendor = $row.find('.select2-vendor').val();
        var standardCost = $row.find('.standard-cost').val();
        var quotedCost = $row.find('.quoted-cost').val();
        var comment = $row.find('.comment').val();
        var total = $row.find('.total').val();
        var sell = $row.find('.sell').val();
        var sellTotal = $row.find('.sell-total').val();
        var gross = $row.find('.gross').val();
        var grossP = $row.find('.gross-p').val();

        // Log the extracted data
        console.log("Quantity:", quantity);
        console.log("Item Code:", item_code);
        console.log("Description:", description);
        console.log("Vendor:", vendor);
        console.log("Standard Cost:", standardCost);
        console.log("Quoted Cost:", quotedCost);
        console.log("Comment:", comment);
        console.log("Total:", total);
        console.log("Sell:", sell);
        console.log("Sell Total:", sellTotal);
        console.log("Gross:", gross);
        console.log("Gross %:", grossP);

        data = {
          quantity: quantity,
          item_code: item_code,
          description: description,
          vendor: vendor,
          standardCost: standardCost,
          quotedCost: quotedCost,
          comment: comment,
        }

        $.ajax({
          url: add_pro,
          type: 'POST',
          data: data,
          headers: {
            'X-CSRFToken': "{{ csrf_token }}",
          },
          success: function(response) {
            console.log('API call success:', response);
            $(".save").css('display', 'none');
            toastr.success(response.message, 'Success', {
              closeButton: true,
              progressBar: true,
              positionClass: 'toast-bottom-right',
              timeOut: 6000
            });
          },
          error: function(xhr, status, error) {
            console.error('API call error:', status, error);
            toastr.error(xhr.responseJSON.message, 'Error', {
              closeButton: true,
              progressBar: true,
              positionClass: 'toast-bottom-right',
              timeOut: 6000
            });
          }
        });

    });
  });

  function copyTableRow(rowId) {
      console.log("Copying table rows...");

      // Log the rowId to check if it's correct
      console.log("Row ID Passed:", rowId);

      var totalRows = parseInt(document.getElementById("totalRows").value, 10);
      console.log("Total Rows:", totalRows);

      if (isNaN(totalRows) || totalRows < 1) {
          totalRows = 1;
      }

      var tableBody = document.getElementById("tableBody");
      console.log("Table Body:", tableBody);

      var rowToCopy = document.getElementById(rowId);
      console.log("Row to Copy:", rowToCopy);

      if (!rowToCopy) {
          console.error("Row with ID '" + rowId + "' not found.");
          return;
      }

      for (var i = 0; i < totalRows; i++) {
          var clonedRow = rowToCopy.cloneNode(true);

          // Remove ID and adjust class for cloned rows
          clonedRow.removeAttribute('id');
          clonedRow.classList.add('dynamic-row');

          // Update input names and IDs to ensure they are unique
          var inputs = clonedRow.querySelectorAll('input, select');
          inputs.forEach(function(input, index) {
              var newName = input.name ? input.name.replace(/\d+/, totalRows + i + 1) : '';
              var newId = input.id ? input.id.replace(/\d+/, totalRows + i + 1) : '';
              input.name = newName;
              input.id = newId;
              input.value = '';
          });

          tableBody.appendChild(clonedRow);
          console.log("Row appended to table body");

          // Increment totalRows
          totalRows++;
          document.getElementById("totalRows").value = totalRows;
      }
    }

// END Copy Product Row based on model value-->


// BEGIN compare standardCost with productCost
  function checkCostEquality(standardCostId, productCostId) {
    var standardCostElement = document.getElementById(standardCostId);
    var productCostInput = document.getElementById(productCostId);

    if (standardCostElement && productCostInput) {
        var standardCost = parseFloat(standardCostElement.textContent.trim().replace('$', ''));
        var productCost = parseFloat(productCostInput.value.trim().replace('$', ''));

        if (standardCost !== productCost) {
              productCostInput.classList.add("border-danger", "border-2", "text-danger");
          } else {
              productCostInput.classList.remove("border-danger", "border-2", "text-danger");
          }
      }
  }

  // Initialize cost checks if necessary
  document.addEventListener("DOMContentLoaded", function() {
      // Optional: Run checks on page load for all inputs
      document.querySelectorAll('input[data-standard-cost]').forEach(function(input) {
          var standardCostId = input.getAttribute('data-standard-cost');
          checkCostEquality(standardCostId, input.id);
      });
  });

    $(document).ready(function() {

        const data = [
            { id: '2800-118501', text: '2800-118501' },
            { id: '2800-118534', text: '2800-118534' },
            { id: '2803-118501', text: '2803-118501' }
        ];

        $('.mySelect2').select2({
            tags: true, // Enable tagging
            data: data,
            placeholder: 'Select tasks',
            allowClear: true
        });

        $('.mySelect2').on('select2:select', function(e) {
          const selectedData = e.params.data;

          // Check if the selected value is in the predefined data
          const isCustom = !data.some(item => item.id === selectedData.id);

          if (isCustom) {
              // Add new custom option if it does not exist
              const newOption = new Option(selectedData.id, selectedData.id, true, true);
              $('.mySelect2').append(newOption).trigger('change');

              // Clear other fields
              $('.new_prod input[type="text"]').val('');
              $('.mySelect3').val(null).trigger('change');
          } else {
              // Optionally handle cases where the value is in predefined data
              console.log('Selected predefined value:', selectedData.id);
          }
        });
    });

    $(document).ready(function() {

      const data = [
        { id: 'Ball Valve Riser 3/4" FHTxMHT', text: 'Ball Valve Riser 3/4" FHTxMHT' },
        { id: 'FIGURE 8 062', text: 'FIGURE 8 062' },
      ];

      $('.mySelect3').select2({
          tags: true, // Enable tagging
          data: data,
          placeholder: 'Select tasks',
          allowClear: true
      });

      $('.mySelect3').on('select2:select', function(e) {
        const selectedData = e.params.data;

        // Check if the selected value is in the predefined data
        const isCustom = !data.some(item => item.id === selectedData.id);

        if (isCustom) {
            // Add new custom option if it does not exist
            const newOption = new Option(selectedData.id, selectedData.id, true, true);
            $('.mySelect3').append(newOption).trigger('change');

            // Clear other fields
            $('.new_prod input[type="text"]').val('');
            $('.mySelect2').val(null).trigger('change');
        } else {
            // Optionally handle cases where the value is in predefined data
            console.log('Selected predefined value:', selectedData.id);
        }
      });
    });

// <!-- Search -->

// <!-- Item code -->
    $(document).ready(function() {
        $('.select2-item-code').select2({
            placeholder: 'Select Item Code',
            ajax: {
                url: item_code_url,
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        q: params.term
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results
                    };
                },
                cache: true
            }
        });

        function updateDescription(value, id) {
          var $select2Element = $(`select[data-id="${id}"].select2-item-description.js-example-programmatic.form-control`);

          // Initialize Select2
          $select2Element.select2({
              ajax: {
                  url: '{% url "proposal_app:opportunity:item-description-search" %}',
                  dataType: 'json',
                  delay: 250,
                  data: function(params) {
                      return {
                          q: value
                      };
                  },
                  processResults: function(data) {
                      return {
                          results: data.results
                      };
                  },
                  cache: true
              }
          });

          // When Select2 is initialized, set the selected value
          $select2Element.on('select2:open', function() {
              setTimeout(function() {
                  $select2Element.val(value).change();
              }, 100);
          });
        }

        $(document).on('change', '.select2-item-code', function(e) {

          // item code
          var $input = $(e.target);
          var id = $input.data("id");
          console.log("id", id);

          var value = $input.val();
          console.log("value",value);

          // Payload data
          data = {
            value: value,
          }

          $.ajax({
            url: item_code_url,
            type: 'POST',
            data: data,
            headers: {
              'X-CSRFToken': "{{ csrf_token }}",
            },
            success: function(response) {
              console.log('API call success:', response);
              if (response.code == 200) {
                console.log("description", response.description);
                console.log("std_cost", response.std_cost);
                updateDescription(response.description, id);
                var $stdCostField = $(`input[data-id="${id}"][id="std_cost"]`);
                $stdCostField.val(response.std_cost);
              }
            },
            error: function(xhr, status, error) {
              console.log("Error:", error);
            }
          });
        });
    });

  // <!-- Item Description -->
    $(document).ready(function() {
      $('.select2-item-description').select2({
          placeholder: 'Select Item description',
          ajax: {
              url: item_description_url,
              dataType: 'json',
              delay: 250,
              data: function (params) {
                  return {
                      q: params.term
                  };
              },
              processResults: function (data) {
                  return {
                      results: data.results
                  };
              },
              cache: true
          }
      });
    });

  // <!-- Vendor -->
    $(document).ready(function() {
        $('.select2-vendor').select2({
            placeholder: 'Select Vendor Name',
            ajax: {
                url: vendor_url,
                dataType: 'json',
                delay: 250,  // Add a delay for better UX
                data: function (params) {
                    return {
                        q: params.term
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results
                    };
                },
                cache: true
            }
        });
    });

  // <!-- Task -->
    $(document).ready(function() {
          $('.select2-task').select2({
              containerCss: { width: "150px" },
              dropdownAutoWidth: true,  // Ensure dropdown respects the width
              width: 'resolve',
              placeholder: 'Select Task Name',
              ajax: {
                  url: task_url,
                  dataType: 'json',
                  delay: 250,
                  data: function (params) {
                      return {
                          q: params.term,
                          document_number: "{{ opportunity.document_number }}",
                      };
                  },
                  processResults: function (data) {
                      return {
                          results: data.results
                      };
                  },
                  cache: true
              }
          });
      });

  // <!-- Labour Task -->
    $(document).ready(function() {
          $('.select2-labor-task').select2({
              containerCss: { width: "150px" },
              dropdownAutoWidth: true,
              width: 'resolve',
              placeholder: 'Select Task Name',
              ajax: {
                  url: labor_task_url,
                  dataType: 'json',
                  delay: 250,
                  data: function (params) {
                      return {
                          q: params.term
                      };
                  },
                  processResults: function (data) {
                      return {
                          results: data.results
                      };
                  },
                  cache: true
              }
          });
      });
// <!-- Search -->

// <!-- Assigned Product Htmx -->
  $(document).on('click', '.htmx-trigger-btn-assign-prod' , function (e) {

    var url = $(this).data('url');
    htmx.ajax('GET',
        url,
        {
          target:'#model-assign',
          swap:'innerHTML',
    }).then(() => {
        $('#assign-prod').toggleClass('hidden');
    })
  });

// <!-- Delete Assigned Product -->
  $(document).on('click', '.assign-prod-delete-btn', function (e) {
    var id = $(this).data("id")
    var prod_name = $(this).data("title")
    if (prod_name == "None") {
      prod_name = ""
    }
    var url = $(this).data("url")
    var delete_ele = $(this)

    Swal.fire({
      html: `Are you sure you want to delete <b>${prod_name}</b>?`,
      icon: 'question',
      showCloseButton: true,
      showCancelButton: true,
      confirmButtonColor: "#7442DB",

    }).then((result) => {

      if (result.isConfirmed) {
        $(this).closest('tr').remove();
        $.ajax({
          type: "POST",
          url: url,
          data: {
            "id": id,
            "csrfmiddlewaretoken": '{{ csrf_token }}'
          },
          success: function (data) {
            console.log("", data);
            toastr.info(data.message, 'Info', {
              closeButton: true,
              progressBar: true,
              positionClass: 'toast-bottom-right',
              timeOut: 6000
            });
          }
        });
      }else {
            Swal.fire("Cancel delete", "", "info");
      }
    });
  });

// <!-- Update Assigned Product -->

  // Input Fields
  $(document).ready(function() {
    $(".quantity, .vendor-quoted-cost, .comment").on("keydown", function(e) {

      if (e.key === 'Enter' || e.keyCode === 13) {
        e.preventDefault();

        var $input = $(e.target);
        var id = $input.data("id");
        var value = $input.val();
        var inputType = '';

        // Determine the input type based on the class
        if ($input.hasClass("quantity")) {
          inputType = 'quantity';
        } else if ($input.hasClass("vendor-quoted-cost")) {
          inputType = 'vendor-quoted-cost';
        } else if ($input.hasClass("comment")) {
          inputType = 'comment';
        }

        // Log the values based on the input type
        console.log(inputType.charAt(0).toUpperCase() + inputType.slice(1) + " Id:", id);
        console.log(inputType.charAt(0).toUpperCase() + inputType.slice(1) + " Value:", value);

        // AJAX call to a single endpoint
        $.ajax({
          url: update_product_fields_url,
          type: 'POST',
          data: {
            type: inputType,
            id: id,
            value: value
          },
          headers: {
            'X-CSRFToken': "{{ csrf_token }}",
          },
          success: function(response) {
            console.log('API call success:', response);
            toastr.success(response.message, 'Success', {
              closeButton: true,
              progressBar: true,
              positionClass: 'toast-bottom-right',
              timeOut: 6000
            });
          },
          error: function(xhr, status, error) {
            console.error('API call error:', status, error);
            toastr.error(xhr.responseJSON.message, 'Error', {
              closeButton: true,
              progressBar: true,
              positionClass: 'toast-bottom-right',
              timeOut: 6000
            });
          }
        });
      }
    });
  });

  // Select Fields
  $(document).ready(function() {
    $(".select2-vendor, .select2-task, .select2-labor-task").on("change", function(e) {
      var $input = $(e.target);
      var id = $input.data("id");
      console.log("id", id);

      var value = $input.val();
      console.log("value",value);

      var inputType = '';

      if ($input.hasClass("select2-vendor")){
        inputType = 'vendor';
      } else if ($input.hasClass("select2-task")){
        inputType = 'task';
      } else if ($input.hasClass("select2-labor-task")){
        inputType = 'labor-task';
      }

      // Log the values based on the input type
      console.log(inputType.charAt(0).toUpperCase() + inputType.slice(1) + " Id:", id);
      console.log(inputType.charAt(0).toUpperCase() + inputType.slice(1) + " Value:", value);

      // AJAX call to a single endpoint
      $.ajax({
        url: update_product_fields_url,
        type: 'POST',
        data: {
          type: inputType,
          id: id,
          value: value
        },
        headers: {
          'X-CSRFToken': "{{ csrf_token }}",
        },
        success: function(response) {
          console.log('API call success:', response);
          toastr.success(response.message, 'Success', {
            closeButton: true,
            progressBar: true,
            positionClass: 'toast-bottom-right',
            timeOut: 6000
          });
        },
        error: function(xhr, status, error) {
          console.error('API call error:', status, error);
          toastr.error(xhr.responseJSON.message, 'Error', {
            closeButton: true,
            progressBar: true,
            positionClass: 'toast-bottom-right',
            timeOut: 6000
          });
        }
      });
    });
  });

// <!-- Add Task Htmx -->
  $(document).on('click', '.htmx-trigger-btn-add-task' , function (e) {

    var url = $(this).data('url');
    htmx.ajax('GET',
        url,
        {
          target:'#model-add-task',
          swap:'innerHTML',
    }).then(() => {
        $('#add-task').toggleClass('hidden');
    })
  });

  document.body.addEventListener('htmx:beforeSwap', function(evt) {

    if(evt.detail.xhr.status === 200){
        // console.log("evt.detail.xhr.status", evt.detail.xhr.status)
        // console.log("evt.detail.xhr.response", evt.detail.xhr.response)
        $("#add-task").modal('hide');
        $("#add-task .modal-body").html('');

        // Parse the JSON response
        var response = JSON.parse(evt.detail.xhr.response);

        if (response.status === 'success') {
          window.location.reload();
        }
    }
  });