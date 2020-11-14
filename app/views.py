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
        return JsonResponse({"message": "only POST request is entertained"})


def visualization(request):
    if request.method == "GET":
        # csv_file = request.FILES["csv_file"]
        csv_file = "dataset.csv"
        data = pd.read_csv(csv_file, encoding="unicode_escape")
        # file_name = request.POST.get('file_name')
        data = data.fillna(0)
        # data.to_csv('{}.csv'.format(file_name), index=False)
        top_rows = data.head(10).to_dict()
        shape = list(data.shape)
        memory = (sys.getsizeof(data) / 1024) / 1024

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

        data_types_dict_count["date"] = 1
        for i, row in data.iterrows():
            sample_data = row.to_dict()
            break

        for k, v in sample_data.items():
            try:
                dt = parser.parse(v)
                data_types_dict[k] = "datetime"
            except:
                continue

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
            dt = parser.parse(row[date_type_field])
            data[date_type_field][index] = dt

        data = data.sort_values(date_type_field).reset_index(drop=True)

        for index, row in data.iterrows():
            dt = row["ORDERDATE"]

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
            elif data_types_dict[k] == "int" or data_types_dict[k] == "float":
                field_summary[k]["populated_ratio"] = not_null[k]
                field_summary[k]["unique_values"] = len(data[k].unique())
                field_summary[k]["mean"] = data[k].mean()
                field_summary[k]["std"] = data[k].std()
                field_summary[k]["min"] = data[k].min()
                field_summary[k]["max"] = data[k].max()
                unique_items_count_for_str_fields[k] = len(data[k].unique())
            elif data_types_dict[k] == "datetime":
                field_summary[k]["populated_ratio"] = not_null[k]
                field_summary[k]["unique_values"] = len(data[k].unique())

        unique_items_count_for_str_fields_sorted = dict(
            sorted(unique_items_count_for_str_fields.items(), key=lambda x: x[1])
        )
        unique_items_count_for_str_fields_sorted

        corr_data = data.corr(method="pearson").to_dict()

        field_summary

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

        numerical_field = "MSRP"
        gb1 = data.groupby([parent, child]).agg(
            {numerical_field: ["mean", "sum", "count"]}
        )
        # print(gb1)

        # unique_items_count_for_str_fields_sorted

        # for name, group in gb1:
        #     print(name, group)

        gb2 = data.groupby([parent, child, grand_child]).agg(
            {numerical_field: ["mean", "sum", "count"]}
        )
        # print(gb2)

        gb3 = data.groupby(["year_index", "month_index", "week_index"]).agg(
            {numerical_field: ["mean", "sum", "count"]}
        )
        # print(gb3)

        # pie chart (5 fields from str hierarchy)
        gb4 = data.groupby([parent]).agg({numerical_field: ["sum"]})

        return render(
            request,
            "visualization.html",
            {
                "top_rows": top_rows,
                "shape": shape,
                "memory": memory,
                "corr_data": corr_data,
                "data_types_dict_count": dict(data_types_dict_count),
            },
        )

    elif request.method == "POST":
        # random_name = request.body['random_name']
        # print(random_name)
        if "csv_file" in request.FILES:
            csv_file = request.FILES["csv_file"]
            data = pd.read_csv(csv_file, encoding="unicode_escape")
            file_name = request.POST.get("file_name")
        else:
            file_name = request.POST.get("file_name")
            data = pd.read_csv("{}.csv".format(file_name), encoding="unicode_escape")

        all_columns = list(data)

        if "mappings" in request.POST:
            mappings = request.POST.get("mappings")

        data = data.fillna(0)
        data.to_csv("{}.csv".format(file_name), index=False)
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

        data_types_dict_count["date"] = 1
        for i, row in data.iterrows():
            sample_data = row.to_dict()
            break

        for k, v in sample_data.items():
            try:
                dt = parser.parse(v)
                data_types_dict[k] = "datetime"
            except:
                continue

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
            dt = parser.parse(row[date_type_field])
            data[date_type_field][index] = dt

        data = data.sort_values(date_type_field).reset_index(drop=True)

        for index, row in data.iterrows():
            dt = row["ORDERDATE"]

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
            elif data_types_dict[k] == "int" or data_types_dict[k] == "float":
                field_summary[k]["populated_ratio"] = not_null[k]
                field_summary[k]["unique_values"] = len(data[k].unique())
                field_summary[k]["mean"] = data[k].mean()
                field_summary[k]["std"] = data[k].std()
                field_summary[k]["min"] = data[k].min()
                field_summary[k]["max"] = data[k].max()
                unique_items_count_for_str_fields[k] = len(data[k].unique())
            elif data_types_dict[k] == "datetime":
                field_summary[k]["populated_ratio"] = not_null[k]
                field_summary[k]["unique_values"] = len(data[k].unique())

        unique_items_count_for_str_fields_sorted = dict(
            sorted(unique_items_count_for_str_fields.items(), key=lambda x: x[1])
        )
        unique_items_count_for_str_fields_sorted

        corr_data = data.corr(method="pearson").to_dict()

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

        numerical_field = "MSRP"
        gb1 = data.groupby([parent, child]).agg(
            {numerical_field: ["mean", "sum", "count"]}
        )
        # print(gb1)

        # unique_items_count_for_str_fields_sorted

        # for name, group in gb1:
        #     print(name, group)

        # gb2 = data.groupby([parent, child, grand_child]).agg({numerical_field: ['mean', 'sum', 'count']})
        # print(gb2)

        # gb3 = data.groupby(['year_index', 'month_index', 'week_index']).agg({numerical_field: ['mean', 'sum', 'count']})
        # print(gb3)

        # gb4 = data.groupby([parent]).agg({numerical_field: ['sum']})

        if "field1" in request.POST:
            parent = request.POST.get("field1")
        field1_agg = data.groupby([parent]).agg({numerical_field: ["sum"]})

        if "field2" in request.POST:
            child = request.POST.get("field2")
        field2_agg = data.groupby([child]).agg({numerical_field: ["sum"]})

        if "field3" in request.POST:
            grand_child = request.POST.get("field3")
        field3_agg = data.groupby([grand_child]).agg({numerical_field: ["sum"]})

        if "field4" in request.POST:
            great_grand_child = request.POST.get("field4")
        field4_agg = data.groupby([great_grand_child]).agg({numerical_field: ["sum"]})

        if "field5" in request.POST:
            great_great_grand_child = request.POST.get("field5")
        field5_agg = data.groupby([great_great_grand_child]).agg(
            {numerical_field: ["sum"]}
        )

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

        field8 = data.groupby([parent, child, grand_child]).agg(
            {numerical_field: ["sum"]}
        )

        field_8_agg = []
        for k, v in list(field8.to_dict().values())[0].items():
            nested_field = []
            for fields in list(k):
                nested_field.append(fields)
            nested_field.append(v)
            field_8_agg.append(nested_field)

        sb_1 = (
            data.groupby([parent, child, grand_child, great_grand_child])
            .agg({numerical_field: ["sum"]})
            .to_dict()
        )

        sb_2 = (
            data.groupby([parent, child, grand_child])
            .agg({numerical_field: ["sum"]})
            .to_dict()
        )
        sb_3 = data.groupby([parent, child]).agg({numerical_field: ["sum"]}).to_dict()

        sb_4 = data.groupby([parent]).agg({numerical_field: ["sum"]}).to_dict()

        u_parents = sorted(list(set(data[parent].dropna())))
        u_children = sorted(list(set(data[child].dropna())))
        u_grand_children = sorted(list(set(data[grand_child].dropna())))
        u_great_grand_children = sorted(list(set(data[great_grand_child].dropna())))

        sb_ids = []
        sb_labels = []
        sb_values = []
        sb_parents = []
        for p in u_parents:
            sb_values.append(sb_4[("MSRP", "sum")][p])
            sb_labels.append(p)
            sb_parents.append("")
            sb_ids.append(p)
        for p in u_parents:
            for i, c in enumerate(u_children):
                sb_ids.append(str(p) + str(c))
                sb_parents.append(p)
                sb_labels.append(c)
                sb_values.append(sb_3[("MSRP", "sum")][tuple([p, c])])
                for gc in u_grand_children:
                    try:
                        sb_values.append((sb_2[("MSRP", "sum")][tuple([p, c, gc])]))
                    except:
                        sb_values.append(1)
                    sb_labels.append(gc)
                    sb_parents.append(str(p) + str(c))
                    sb_ids.append(str(p) + str(c) + str(gc))
                    for ggc in u_great_grand_children:
                        try:
                            sb_values.append(
                                (sb_1[("MSRP", "sum")][tuple([p, c, gc, ggc])])
                            )
                        except:
                            sb_values.append(1)
                        sb_labels.append(ggc)
                        sb_parents.append(str(p) + str(c) + str(gc))
                        sb_ids.append(str(p) + str(c) + str(gc) + str(ggc))

        hist_parent_dict = {}
        for u_p in u_parents:
            hist_parent = data[data[parent] == u_p]
            hist_parent_dict[u_p] = list(hist_parent[numerical_field])

        return render(
            request,
            "visualization.html",
            {
                "top_rows": top_rows,
                "shape": shape,
                "memory": memory,
                "file_name": file_name,
                "corr_data": corr_data,
                "data_types_dict_count": dict(data_types_dict_count),
                "column_names": all_columns,
                "field_summary": field_summary,
                "field1_agg": list(field1_agg.to_dict().values())[0],
                "field2_agg": list(field2_agg.to_dict().values())[0],
                "field3_agg": list(field3_agg.to_dict().values())[0],
                "field4_agg": list(field4_agg.to_dict().values())[0],
                "field5_agg": list(field5_agg.to_dict().values())[0],
                "field6_agg": field_6_agg,
                "field7_agg": field_7_agg,
                "field8_agg": field_8_agg,
                # "sb_ids": sb_ids,
                # "sb_labels": sb_labels,
                # "sb_values": sb_values,
                # "sb_parents": sb_parents,
                "hist_parent_dict": hist_parent_dict
            },
        )
