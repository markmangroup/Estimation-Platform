function initialize_datatables() {
    $(table_id).DataTable({
        autoWidth: false,
        order: [[0, 'asc']],
        columnDefs: [
            { orderable: false, targets: targets },
        ],
        processing: true,
        serverSide: true,
        ajax: {
            url: url,
            type: 'GET',
            data: function(d) {
                $.extend(d, set_filters());
            }
        },
        columns: columns
    });
}

function set_filters() {
    return {
        filter_param1: $("#filter1").val(),
        filter_param2: $("#filter2").val()
    };
}

// Reinitialize DataTable when filters change
$(document).ready(function() {
    // Initialize DataTable on page load
    initialize_datatables();

    // Handle filter changes
    $('#filter1, #filter2').on("change", function() {
        $(table_id).DataTable().destroy();  // Destroy the old instance
        initialize_datatables();  // Reinitialize with updated settings
    });
});
