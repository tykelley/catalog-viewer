import pandas as pd
import sqlalchemy
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, CustomJS
from bokeh.models.widgets import TextInput, Select, CheckboxGroup, Panel, Tabs, Button  # DataTable, TableColumn
from bokeh.plotting import figure
from os.path import join, dirname
from sqlalchemy import and_

# Setup data and SQL

engine = sqlalchemy.create_engine('sqlite:///./test.db')
metadata = sqlalchemy.MetaData()
metadata.reflect(bind=engine)
dmo = metadata.tables['dmo']
disk = metadata.tables['disk']
conn = engine.connect()

df = pd.read_sql(sqlalchemy.select([dmo])
                           .where(and_(dmo.c.vmax > 100, dmo.c.dist < 100)),
                 conn)
df2 = pd.read_sql(sqlalchemy.select([disk])
                            .where(and_(disk.c.vmax > 100, disk.c.dist < 100)),
                  conn)
dmo_data = ColumnDataSource(pd.read_sql(sqlalchemy.select([dmo]), conn))
disk_data = ColumnDataSource(pd.read_sql(sqlalchemy.select([disk]), conn))
dmo_source = ColumnDataSource(data=df)
disk_source = ColumnDataSource(data=df2)
dmo_scatter = ColumnDataSource(data={'x': [], 'y': [], 'host_id': []})
disk_scatter = ColumnDataSource(data={'x': [], 'y': [], 'host_id': []})
dmo_line = ColumnDataSource(data={'x': [], 'y': []})
disk_line = ColumnDataSource(data={'x': [], 'y': []})

# Build Bokeh inputs and callbacks

col_exclude = ['x', 'y', 'z', 'index', 'host_id']
col_allow = [i for i in df.columns if i not in col_exclude]
default_query = "where vmax > 100 and dist < 100"

sql_query = TextInput(value=default_query, title='SQL filter:')
sql_query2 = TextInput(value=default_query, title='SQL filter:')
x_col = Select(title="X-axis Data:", value="vmax", options=col_allow)
y_col = Select(title="Y-axis Data:", value="mvir", options=col_allow)
log_axes = CheckboxGroup(labels=["Log(x)", "Log(y)"], active=[], inline=True)
plot_type = Select(title="Standard plots:", value="Infall",
                   options=["Infall", "Mvir", "Vmax", "Vpeak", "Pericenter"])

labels_dict = dict(vmax='Vmax (km/s)', mvir='Mvir (M_sun)',
                   rvir='Rvir (kpc)', dist='Dist from MW (kpc)',
                   peri='Pericenter (kpc)', vpeak='Vpeak (km/s)',
                   vr='Radial Velocity (km/s)', infall='Infall Time (Gyrs)',
                   vtan='Tangential Velocity (km/s)',)
hover = HoverTool(tooltips=[('Host', '@host_id'),
                            ('{}'.format(x_col.value), '@x'),
                            ('{}'.format(y_col.value), '@y')])

p = figure(x_axis_label="Vmax (km/s)", y_axis_label="Mvir (M_sun)")
p.circle('x', 'y', source=dmo_scatter,
         color='black',
         legend='DMO',
         size=7)
p.circle('x', 'y', source=disk_scatter,
         color='magenta',
         legend='Disk',
         size=7,
         fill_alpha=0.5)
p.add_tools(hover)
p.legend.location = 'top_left'
p.legend.click_policy = 'hide'
p.legend.background_fill_alpha = 0.5

p2 = figure()
p2.line('x', 'y', source=dmo_line, color='black', legend='DMO', line_width=3)
p2.line('x', 'y', source=disk_line, color='magenta', legend='Disk', line_width=3)
p2.legend.click_policy = 'hide'


def query_change(attr, old, new):
    """Applies SQL query to both the DMO and Disk tables."""
    s = 'select * from dmo ' + new
    s2 = 'select * from disk ' + new

    # Make sure both fields show the same value
    sql_query.value = new
    sql_query2.value = new

    new_df = pd.read_sql(s, conn)
    dmo_source.data = {i: new_df[i] for i in new_df.columns}
    new_df = pd.read_sql(s2, conn)
    disk_source.data = {i: new_df[i] for i in new_df.columns}
    column_change([], [], [])
    create_line_plot([], [], plot_type.value)


def update_plot_data():
    dmo_scatter.data = {
        'x': dmo_source.data[x_col.value],
        'y': dmo_source.data[y_col.value],
        'host_id': dmo_source.data['host_id'].astype(int),
    }
    disk_scatter.data = {
        'x': disk_source.data[x_col.value],
        'y': disk_source.data[y_col.value],
        'host_id': disk_source.data['host_id'].astype(int),
    }


def column_change(attr, old, new):
    """Select new columns to plot."""
    dmo_x = dmo_source.data[x_col.value]
    dmo_y = dmo_source.data[y_col.value]
    disk_x = disk_source.data[x_col.value]
    disk_y = disk_source.data[y_col.value]

    # Suppress errors from log-scaling values
    old_set = np.seterr(divide='ignore', invalid='ignore')

    if (0 in log_axes.active):
        p.xaxis.axis_label = "Log10  " + labels_dict[x_col.value]
        dmo_x = np.log10(dmo_x)
        disk_x = np.log10(disk_x)
    else:
        p.xaxis.axis_label = labels_dict[x_col.value]

    if (1 in log_axes.active):
        p.yaxis.axis_label = "Log10  " + labels_dict[y_col.value]
        dmo_y = np.log10(dmo_y)
        disk_y = np.log10(disk_y)
    else:
        p.yaxis.axis_label = labels_dict[y_col.value]

    hover.tooltips = [('Host', '@host_id'),
                      ('{}'.format(x_col.value), '@x'),
                      ('{}'.format(y_col.value), '@y')]

    _ = np.seterr(**old_set)

    dmo_scatter.data = {
        'x': dmo_x,
        'y': dmo_y,
        'host_id': dmo_source.data['host_id'].astype(int),
    }
    disk_scatter.data = {
        'x': disk_x,
        'y': disk_y,
        'host_id': disk_source.data['host_id'].astype(int),
    }


def scale_axes(attr, old, new):
    """Applies log-scaling using checkboxes."""
    dmo_x = dmo_scatter.data['x']
    dmo_y = dmo_scatter.data['y']
    dmo_id = dmo_scatter.data['host_id']
    disk_x = disk_scatter.data['x']
    disk_y = disk_scatter.data['y']
    disk_id = disk_scatter.data['host_id']

    # Suppress errors from log-scaling values
    old_set = np.seterr(divide='ignore', invalid='ignore')

    # log_axes.active contains the index of checked options
    # e.g. log_axes.active == [0] -> take log of x-axis
    if (0 in new) and (0 not in old):
        dmo_x = np.log10(dmo_x)
        disk_x = np.log10(disk_x)
        p.xaxis.axis_label = "Log10  " + labels_dict[x_col.value]
    if (0 not in new) and (0 in old):
        dmo_x = dmo_source.data[x_col.value]
        disk_x = disk_source.data[x_col.value]
        p.xaxis.axis_label = labels_dict[x_col.value]

    if (1 in new) and (1 not in old):
        dmo_y = np.log10(dmo_y)
        disk_y = np.log10(disk_y)
        p.yaxis.axis_label = "Log10  " + labels_dict[y_col.value]
    if (1 not in new) and (1 in old):
        dmo_y = dmo_source.data[y_col.value]
        disk_y = disk_source.data[y_col.value]
        p.yaxis.axis_label = labels_dict[y_col.value]

    _ = np.seterr(**old_set)

    dmo_scatter.data = {
        'x': dmo_x,
        'y': dmo_y,
        'host_id': dmo_id,
    }
    disk_scatter.data = {
        'x': disk_x,
        'y': disk_y,
        'host_id': disk_id,
    }


def create_line_plot(attr, old, new):
    """Generates what I consider the standard plots for this work."""
    if old == new:
        return

    old_set = np.seterr(divide='ignore', invalid='ignore')

    if new == "Infall":
        t = dmo_source.data['infall'][dmo_source.data['infall'] < 13.8]
        hist, edges = np.histogram(t, bins=100, range=(0, 13))
        hist = (np.sum(hist) - np.cumsum(hist))/np.sum(hist)
        dmo_line.data = {'x': edges[:-1],
                         'y': hist}
        t = disk_source.data['infall'][disk_source.data['infall'] < 13.8]
        hist, edges = np.histogram(t, bins=100, range=(0, 13))
        hist = (np.sum(hist) - np.cumsum(hist))/np.sum(hist)
        disk_line.data = {'x': edges[:-1],
                          'y': hist}
        p2.xaxis.axis_label = labels_dict['infall']
        p2.yaxis.axis_label = ""
    elif new == "Mvir":
        t = np.log10(dmo_source.data['mvir'][dmo_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        dmo_line.data = {'x': edges[:-1],
                         'y': hist}
        t = np.log10(disk_source.data['mvir'][disk_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        disk_line.data = {'x': edges[:-1],
                          'y': hist}
        p2.xaxis.axis_label = "Log10  " + labels_dict['mvir']
        p2.yaxis.axis_label = ""
    elif new == "Vmax":
        t = np.log10(dmo_source.data['vmax'][dmo_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        dmo_line.data = {'x': edges[:-1],
                         'y': hist}
        t = np.log10(disk_source.data['vmax'][disk_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        disk_line.data = {'x': edges[:-1],
                          'y': hist}
        p2.xaxis.axis_label = "Log10  " + labels_dict['vmax']
        p2.yaxis.axis_label = ""
    elif new == "Vpeak":
        t = np.log10(dmo_source.data['vpeak'][dmo_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        dmo_line.data = {'x': edges[:-1],
                         'y': hist}
        t = np.log10(disk_source.data['vpeak'][disk_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        disk_line.data = {'x': edges[:-1],
                          'y': hist}
        p2.xaxis.axis_label = "Log10  " + labels_dict['vpeak']
        p2.yaxis.axis_label = ""
    elif new == "Pericenter":
        t = (dmo_source.data['peri'][dmo_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.cumsum(hist)/hist.sum()
        dmo_line.data = {'x': edges[:-1],
                         'y': hist}
        t = (disk_source.data['peri'][disk_source.data['dist'] > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.cumsum(hist)/hist.sum()
        disk_line.data = {'x': edges[:-1],
                          'y': hist}
        p2.xaxis.axis_label = labels_dict['peri']
        p2.yaxis.axis_label = ""

    _ = np.seterr(**old_set)


sql_query.on_change('value', query_change)
sql_query2.on_change('value', query_change)
log_axes.on_change('active', scale_axes)
x_col.on_change('value', column_change)
y_col.on_change('value', column_change)
plot_type.on_change('value', create_line_plot)

button_dmo_sub = Button(label="Download DMO Query", button_type="primary")
button_dmo_all = Button(label="Download DMO Catalog", button_type="primary")
button_disk_sub = Button(label="Download Disk Query", button_type="danger")
button_disk_all = Button(label="Download Disk Catalog", button_type="danger")
button_dmo_all.callback = CustomJS(args=dict(source=dmo_data, fname='pelvis_dmo_all.csv'),
                                   code=open(join(dirname(__file__), "download.js")).read())
button_dmo_sub.callback = CustomJS(args=dict(source=dmo_source, fname='pelvis_dmo_query.csv'),
                                   code=open(join(dirname(__file__), "download.js")).read())
button_disk_all.callback = CustomJS(args=dict(source=disk_data, fname='pelvis_disk_all.csv'),
                                    code=open(join(dirname(__file__), "download.js")).read())
button_disk_sub.callback = CustomJS(args=dict(source=disk_source, fname='pelvis_disk_query.csv'),
                                    code=open(join(dirname(__file__), "download.js")).read())
button_list = [button_dmo_sub, button_dmo_all, button_disk_sub, button_disk_all]
download_buttons = widgetbox(button_list, sizing_mode='scale_both')

# Setup the page layout

tab1 = Panel(child=row(column(sql_query, log_axes, x_col, y_col, download_buttons), p), title='Explore')
tab2 = Panel(child=row(column(sql_query2, plot_type), p2), title='Relations')
tabs = Tabs(tabs=[tab1, tab2])

curdoc().add_root(tabs)
curdoc().title = 'Sim App Test'

update_plot_data()
create_line_plot([], [], "Infall")
