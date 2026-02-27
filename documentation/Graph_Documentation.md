Graph Implementation Documentation

**SETUP**

* Frontend requires Recharts to build charts.
* The following imports are required:

```
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area
} from "recharts";
```

**STEP 1: FETCH**

To implement, use the following endpoint to request data:

'GET /api/projects/{project_id}/stats'

This will require credentials: “include” to run. A successful sample response will look like this:

```
{
  "success": true,
  "data": {
    "project_id": 272,
    "project_title": "Bird Watch — Spring 2024",
    "total_observations": 9,
    "fields": [
      {
        "field_id": 392,
        "field_name": "bird_species",
        "field_label": "Bird Species (Common Name)",
        "field_type": "text",
        "chart_type": "none",
        "stats": {
          "count": 8
        }
      },
      {
        "field_id": 393,
        "field_name": "count",
        "field_label": "Bird Count (Number)",
        "field_type": "number",
        "chart_type": "bar",
        "stats": {
          "count": 9,
          "min": 2.0,
          "max": 12.0,
          "mean": 5.22
        }
      },
      {
        "field_id": 394,
        "field_name": "observation_date",
        "field_label": "Observation Date (Date)",
        "field_type": "date",
        "chart_type": "line",
        "stats": {
          "timeline": [
            { "date": "2024-02-11", "count": 3 },
            { "date": "2024-02-14", "count": 2 },
            { "date": "2024-02-16", "count": 1 },
            { "date": "2024-02-18", "count": 2 },
            { "date": "2024-02-20", "count": 1 }
          ]
        }
      },
      {
        "field_id": 395,
        "field_name": "was_singing",
        "field_label": "Was Singing? (Checkbox/Boolean)",
        "field_type": "checkbox",
        "chart_type": "pie",
        "stats": {
          "frequency": [
            { "value": "true",  "count": 6 },
            { "value": "false", "count": 3 }
          ]
        }
      },
      {
        "field_id": 396,
        "field_name": "behaviors",
        "field_label": "Observed Behaviors (Multiselect)",
        "field_type": "multiselect",
        "chart_type": "bar",
        "stats": {
          "frequency": [
            { "value": "Feeding", "count": 7 },
            { "value": "Flying",  "count": 6 },
            { "value": "Singing", "count": 5 },
            { "value": "Nesting", "count": 3 },
            { "value": "Bathing", "count": 2 }
          ]
        }
      },
      {
        "field_id": 397,
        "field_name": "weather",
        "field_label": "Weather Condition (Dropdown)",
        "field_type": "dropdown",
        "chart_type": "pie",
        "stats": {
          "frequency": [
            { "value": "Sunny",  "count": 4 },
            { "value": "Cloudy", "count": 2 },
            { "value": "Rainy",  "count": 2 },
            { "value": "Snowy",  "count": 1 }
          ]
        }
      },
      {
        "field_id": 398,
        "field_name": "bad_options",
        "field_label": "Bad Options (Array Sent)",
        "field_type": "dropdown",
        "chart_type": "bar",
        "stats": {
          "frequency": [
            { "value": "a", "count": 4 },
            { "value": "b", "count": 3 },
            { "value": "c", "count": 2 },
            { "value": "d", "count": 1 }
          ]
        }
      },
      {
        "field_id": 399,
        "field_name": "notes",
        "field_label": "Observation Notes (Textarea)",
        "field_type": "textarea",
        "chart_type": "none",
        "stats": {
          "count": 7
        }
      },
      {
        "field_id": 400,
        "field_name": "observation_time",
        "field_label": "Observation Time (Time)",
        "field_type": "time",
        "chart_type": "none",
        "stats": {
          "count": 9
        }
      }
    ]
  }
}
```

**STEP 2: TRANSFORM**

This response includes every field type. You will have to transform them into a Recharts-friendly format. Here is sample code on how to transform everything from the sample response above:

* field_type: text / textarea/ time into TextCard. Can read the count directly:

```
const { count } = field.stats;
```

* field_type: number into NumericCard. Also does not need a transformation:

```
const { count, min, max, mean } = field.stats;
```

* field_type: date into LineChartCard. No transforming, can use keys:

```
const data = field.stats.timeline.map(t => ({
  date:  t.date,
  count: t.count
}));
```

* field_type: checkbox into PieChartCard. Need to rename keys and convert “true” or “false” strings to “Yes” or “No” to render properly:

```
const data = field.stats.frequency.map(f => ({
  name:  f.value === "true" ? "Yes" : "No",
  value: f.count
}));
```

* field_type: dropdown / radio into either PieChartCard or BarCartCard. For types where it can be either a pie chart or bar graph, the backend formats it automatically. If a field has more than 3 options, it turns into a bar graph, if it has 3 or less it formats it as a pie chart. Need to rename keys:

```
const data = field.stats.frequency.map(f => ({
  name:  f.value,
  value: f.count
}));
```

* multiselect into BarChartCard. Just rename, backend expands the JSON arrays.

```
const data = field.stats.frequency.map(f => ({
  name:  f.value,
  value: f.count
}));
```

These transformations are found within individual functions in Graph_Example.html. Each function also includes return code that renders and styles the chart itself.

**STEP 3: DISPATCH**

A separate function (FieldChart in Graph_Example.html) receives each field and routes it to a separate component based on chart_type.

FieldChart Code:

```
function FieldChart({ field }) {
  const { chart_type, field_type } = field;
  if (field_type === "number")  return <NumericCard   field={field} />;
  if (chart_type === "pie")     return <PieChartCard  field={field} />;
  if (chart_type === "bar")     return <BarChartCard  field={field} />;
  if (chart_type === "line")    return <LineChartCard field={field} />;
  return <TextCard field={field} />;
}
```

If you refer to the Graph_Example.html in the documentation folder on my GitHub, you can see where I set up functions for all these chart types. In the same function, the data is returned and formatted separately.

**STEP 4: RENDER**

In the body of your page code, you can loop through fields to render each chart. So if you call the endpoint, there are 9 fields, it will generate 9 charts and format it with the previous functions built above.

Graph_Example.html Code:

```
{stats.fields.map((field, i) => (
    #Miscellaneous other code removed
    <FieldChart field={field} />
```


FIELD TYPE REFERENCE:

Field/Chart Types:

* Field Type: number
* Chart Type: bar graph
* Rechart Component: “NumericCard”
* Stats Shape:

'{ count, min, max, mean }'

* Field Type: radio / dropdown
* Chart Type: pie or bar
* Rechart Component: “PieChartCard” or “BarChartCard”
* Stats Shape:

'{ frequency: [{value, count}] }'

* Field Type: checkbox
* Chart Type: pie
* Rechart Component: “PieChartCard”
* Stats Shape:

'{ frequency: [{value: "true"/"false", count}] }'

* Field Type: multiselect
* Chart Type: pie or bar
* Rechart Component: “PieChartCard” or “BarChartCard”
* Stats Shape:

'{ frequency: [{value, count}] }'

* Field Type: date
* Chart Type: line
* Rechart Component: “LineChartCard”
* Stats Shape:

'{ timeline: [{date, count}] }'

* Field Type: text / textarea
* Chart Type: none
* Rechart Component: “TextCard”
* Stats Shape:

'{ count }'
