import json
import random
import string
from datetime import datetime
import math
import numpy as np
import pandas as pd
from dateutil import parser
import sys
from collections import Counter

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return render(request, "home.html")


def email(subject, message, recipient_list):
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient_list)


@csrf_exempt
def send_email(request):
    if request.method == "POST":
        body = json.loads(request.body)
        name = body["name"]
        phone = body["phone"]
        user_email = body["email"]
        message = body["message"]
        message = "Name:{}. Phone:{}. Email:{}. Message:{}".format(
            name, phone, user_email, message
        )
        email("Registration Completed", message, ["inquiry@revecy.com"])
        return JsonResponse({"message": "Email sent."})
    else:
        return JsonResponse({"message": "only POST request is entertained"})


def visualization(request):
    if request.method == "GET":
        file_name = "dataset"
        data = pd.read_csv("{}.csv".format(file_name), encoding="unicode_escape")
        mappings = ""

    elif request.method == "POST":
        # random_name = request.body['random_name']
        if "csv_file" in request.FILES:
            csv_file = request.FILES["csv_file"]
            data = pd.read_csv(csv_file, encoding="unicode_escape")
            file_name = request.POST.get("file_name")
        else:
            file_name = request.POST.get("file_name")
            data = pd.read_csv("{}.csv".format(file_name), encoding="unicode_escape")

        if "mappings" in request.POST:
            mappings = request.POST.get("mappings")
        else:
            mappings = ""

        data.to_csv("{}.csv".format(file_name), index=False)
    data = data.fillna(0)
    all_columns = list(data)
    top_rows = data.head(10).to_dict()
    shape = list(data.shape)
    memory = (sys.getsizeof(data) / 1024) / 1024

    # Detecting date types count for all fields
    data_types = data.dtypes
    data_types.to_dict()
    data_types_dict = {}
    data_types_dict_count = Counter()

    for k, v in data_types.items():
        if "int" in str(v):
            data_types_dict[k] = "int"
            data_types_dict_count["int"] += 1
        elif "object" in str(v):
            data_types_dict[k] = "str"
            data_types_dict_count["str"] += 1
        elif "float" in str(v):
            data_types_dict[k] = "float"
            data_types_dict_count["float"] += 1
        elif "bool" in str(v):
            data_types_dict[k] = "bool"
            data_types_dict_count["bool"] += 1
    

    data_types_dict_count["date"] = 1
    for i, row in data.iterrows():
        sample_data = row.to_dict()
        break

    for k, v in sample_data.items():
        try:
            # dt = parser.parse(str(v))
            d = pd.to_datetime(str(v))
            data_types_dict[k] = "datetime"
        except:
            continue
    string_columns = []
    for k, v in data_types_dict.items():
        if v == "str":
            string_columns.append(k)
    
    numerical_columns = []
    for k, v in data_types_dict.items():
        if v == "int":
            numerical_columns.append(k)

    # Detecting date type field
    for k, v in data_types_dict.items():
        if v == "datetime":
            date_type_field = k

    # preparing index for year, month, quarter, week, day
    data["day_index"] = None
    data["week_index"] = None
    data["month_index"] = None
    data["quarter_index"] = None
    data["year_index"] = None

    for index, row in data.iterrows():
        dt = parser.parse(str(row[date_type_field]))
        data[date_type_field][index] = dt

    data = data.sort_values(date_type_field).reset_index(drop=True)

    for index, row in data.iterrows():
        dt = row[date_type_field]

        if index == 0:
            first_month = dt.month
            first_year = dt.year

        current_month = (dt.month - first_month) + ((dt.year - first_year) * 12) + 1
        current_week = ((dt.day // 7) + 1) + ((current_month - 1) * 4)
        current_year = (dt.year - first_year) + 1
        data["year_index"][index] = current_year
        data["week_index"][index] = current_week
        data["month_index"][index] = current_month
        data["quarter_index"][index] = (current_month // 3) + 1
        data["day_index"][index] = ((current_month - 1) * 30) + dt.day

    not_null = data.isnull().sum() / len(data) * 100
    not_null.to_dict()

    unique_items_count_for_str_fields = {}
    field_summary = {}

    for k, v in sample_data.items():
        field_summary[k] = {}
        if data_types_dict[k] == "str":
            field_summary[k]["populated_ratio"] = not_null[k]
            field_summary[k]["unique_values"] = len(data[k].unique())
            unique_items_count_for_str_fields[k] = len(data[k].unique())
        elif data_types_dict[k] == "bool":
            field_summary[k]["populated_ratio"] = not_null[k]
            field_summary[k]["unique_values"] = len(data[k].unique())
            # unique_items_count_for_str_fields[k] = len(data[k].unique())
        elif data_types_dict[k] == "int" or data_types_dict[k] == "float":
            field_summary[k]["populated_ratio"] = not_null[k]
            field_summary[k]["unique_values"] = len(data[k].unique())
            field_summary[k]["mean"] = data[k].mean()
            field_summary[k]["std"] = data[k].std()
            field_summary[k]["min"] = data[k].min()
            field_summary[k]["max"] = data[k].max()
            # unique_items_count_for_str_fields[k] = len(data[k].unique())
        elif data_types_dict[k] == "datetime":
            field_summary[k]["populated_ratio"] = not_null[k]
            field_summary[k]["unique_values"] = len(data[k].unique())

    unique_items_count_for_str_fields_sorted = dict(
        sorted(unique_items_count_for_str_fields.items(), key=lambda x: x[1])
    )
    unique_items_count_for_str_fields_sorted
    corr_data = data.corr(method="pearson").fillna(0).to_dict()

    i = 0
    for k, v in unique_items_count_for_str_fields_sorted.items():
        i += 1
        if i == 1:
            parent = k
        elif i == 2:
            child = k
        elif i == 3:
            grand_child = k
        elif i == 4:
            great_grand_child = k
        elif i == 5:
            great_great_grand_child = k

    numerical_field = numerical_columns[0]
    gb1 = data.groupby([parent, child]).agg(
        {numerical_field: ["mean", "sum", "count"]}
    )

    # Pie chart, Bar chart
    if "field1" in request.POST:
        parent = request.POST.get("field1")
    # else:
    #     parent = "STATUS"
    field1_agg = data.groupby([parent]).agg({numerical_field: ["sum"]})

    if "field2" in request.POST:
        child = request.POST.get("field2")
    # else:
    #     child = "STATUS"
    field2_agg = data.groupby([child]).agg({numerical_field: ["sum"]})

    if "field3" in request.POST:
        grand_child = request.POST.get("field3")
    # else:
    #     grand_child = "STATUS"
    field3_agg = data.groupby([grand_child]).agg({numerical_field: ["sum"]})

    if "field4" in request.POST:
        numerical_field = request.POST.get("field4")

    # Stack bar graph/ line chart
    field6 = data.groupby([parent, child]).agg({numerical_field: ["sum"]})

    field_6_agg = []
    
    for k, v in list(field6.to_dict().values())[0].items():
        nested_field = []
        for fields in list(k):
            nested_field.append(fields)
        nested_field.append(v)
        field_6_agg.append(nested_field)

    field7 = data.groupby([parent, grand_child]).agg({numerical_field: ["sum"]})

    field_7_agg = []
    for k, v in list(field7.to_dict().values())[0].items():
        nested_field = []
        for fields in list(k):
            nested_field.append(fields)
        nested_field.append(v)
        field_7_agg.append(nested_field)

    field8 = data.groupby([child, grand_child]).agg(
        {numerical_field: ["sum"]}
    )

    field_8_agg = []
    for k, v in list(field8.to_dict().values())[0].items():
        nested_field = []
        for fields in list(k):
            nested_field.append(fields)
        nested_field.append(v)
        field_8_agg.append(nested_field)

    # Sunburst
    # sb_1 = (
    #     data.groupby([parent, child, grand_child, great_grand_child])
    #     .agg({numerical_field: ["sum"]})
    #     .to_dict()
    # )

    sb_2 = (
        data.groupby([parent, child, grand_child])
        .agg({numerical_field: ["sum"]})
        .to_dict()
    )
    sb_3 = data.groupby([parent, child]).agg({numerical_field: ["sum"]}).to_dict()

    sb_4 = data.groupby([parent]).agg({numerical_field: ["sum"]}).to_dict()

    u_parents = list(set(data[parent]))
    if 0 in u_parents:
        u_parents.remove(0)
        u_parents = sorted(u_parents)

    u_children = list(set(data[child]))
    if 0 in u_children:
        u_children.remove(0)
        u_children = sorted(u_children)

    u_grand_children = list(set(data[grand_child]))
    if 0 in u_grand_children:
        u_grand_children.remove(0)
        u_grand_children = sorted(u_grand_children)

    u_great_grand_children = list(set(data[great_grand_child]))
    if 0 in u_great_grand_children:
        u_great_grand_children.remove(0)
        u_great_grand_children = sorted(u_great_grand_children)

    sb_ids = []
    sb_labels = []
    sb_values = []
    sb_parents = []

    for p in u_parents:
        sb_values.append(sb_4[(numerical_field, "sum")][p])
        sb_labels.append(p)
        sb_parents.append("")
        sb_ids.append(p)

    for p in u_parents:
        for i, c in enumerate(u_children):
            sb_ids.append(str(p) + str(c))
            sb_parents.append(p)
            sb_labels.append(c)
            try:
                sb_values.append(sb_3[(numerical_field, "sum")][tuple([p, c])])
            except:
                sb_values.append(1)
            for gc in u_grand_children:
                try:
                    sb_values.append((sb_2[(numerical_field, "sum")][tuple([p, c, gc])]))
                except:
                    sb_values.append(1)
                sb_labels.append(gc)
                sb_parents.append(str(p) + str(c))
                sb_ids.append(str(p) + str(c) + str(gc))
                # for ggc in u_great_grand_children:
                #     try:
                #         sb_values.append(
                #             (sb_1[(numerical_field, "sum")][tuple([p, c, gc, ggc])])
                #         )
                #     except:
                #         sb_values.append(1)
                #     sb_labels.append(ggc)
                #     sb_parents.append(str(p) + str(c) + str(gc))
                #     sb_ids.append(str(p) + str(c) + str(gc) + str(ggc))


    # Histogram
    hist_parent_dict = {}
    for u_p in u_parents:
        hist_parent = data[data[parent] == u_p]
        hist_parent_dict[u_p] = list(hist_parent[numerical_field])
    
    hist_children_dict = {}
    for u_c in u_children:
        hist_children = data[data[child] == u_c]
        hist_children_dict[u_c] = list(hist_children[numerical_field])

    hist_grand_children_dict = {}
    for u_g_c in u_grand_children:
        hist_grand_children = data[data[grand_child] == u_g_c]
        hist_grand_children_dict[u_g_c] = list(hist_grand_children[numerical_field])

    # Bubble Plot
    all_numerical_fields = []
    for k, v in data_types_dict.items():
        if v == 'int' and k not in ["year_index", "week_index", "month_index", "quarter_index", "day_index", "QTR_ID", "MONTH_ID", "YEAR_ID"]:
            all_numerical_fields.append(k)
    
    random_numerical_fields = random.sample(all_numerical_fields, 3)

    bubble_plot = {}
    for u_p in u_parents:
        bubble_plot_parent = data[data[parent] == u_p]
        bubble_plot[u_p] = {
            random_numerical_fields[0]: list(bubble_plot_parent[random_numerical_fields[0]]),
            random_numerical_fields[1]: list(bubble_plot_parent[random_numerical_fields[1]]),
            random_numerical_fields[2]: list(bubble_plot_parent[random_numerical_fields[2]])
        }
    print(top_rows)
    return render(
        request,
        "visualization.html",
        {   "parent": parent,
            "child": child,
            "grand_child":grand_child,
            "numerical_field": numerical_field,
            "mappings":mappings,
            "top_rows": top_rows,
            "shape": shape,
            "memory": memory,
            "file_name": file_name,
            "corr_data": corr_data,
            "data_types_dict_count": dict(data_types_dict_count),
            "column_names": string_columns,
            "numerical_columns": numerical_columns,
            "field_summary": field_summary,
            "field1_agg": list(field1_agg.to_dict().values())[0],
            "field2_agg": list(field2_agg.to_dict().values())[0],
            "field3_agg": list(field3_agg.to_dict().values())[0],
            "field6_agg": field_6_agg,
            "field7_agg": field_7_agg,
            "field8_agg": field_8_agg,
            "sb_ids": sb_ids,
            "sb_labels": sb_labels,
            "sb_values": sb_values,
            "sb_parents": sb_parents,
            "hist_parent_dict": hist_parent_dict,
            "hist_children_dict": hist_children_dict,
            "hist_grand_children_dict": hist_grand_children_dict,
            "bubble_plot": bubble_plot,
        },
    )
