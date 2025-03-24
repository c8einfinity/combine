
def get_data_tables_filter(request):
    params = request.params

    columns = []
    if "columns" in params:
        columns = params["columns"]

    order_by = []
    if "order" in params:
        order_by = params["order"]

    filter = []
    search_values = []
    list_of_column_names = []
    search = {"value": ""}

    if "search" in params:
        search = params["search"]
        search_values = search["value"].split(" ")

    for column in columns:
        column_name = column["data"] #check this

        if column["searchable"] and search["value"]:
            list_of_column_names.append(column_name)

        for search_value in search_values:
            if search_value != "":
                filter_value = column_name+" like '%"+search_value+"%'"
                if filter_value not in filter:
                    filter.append(filter_value)
    ordering = []

    if order_by:
        for order in order_by:
            column_name = str(int(order["column"])+1)
            ordering.append(column_name+" "+order["dir"])

    order = ", ".join(ordering)

    where = " or ".join(filter)

    if "start" in params:
        start = params["start"]
    else:
        start = 0

    if "length" in params:
        length = params["length"]
    else:
        length = 10

    return {"length": length, "start" : start, "order_by" : order, "where" :  where}
