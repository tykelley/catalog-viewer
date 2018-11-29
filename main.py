from os.path import join,dirname

import pandas as pd
import sqlalchemy
from sqlalchemy import and_
import numpy as np

from bokeh.io import curdoc
from bokeh.palettes import Category20
from bokeh.layouts import row, column, widgetbox, layout
from bokeh.models import ColumnDataSource, HoverTool, CategoricalColorMapper, CustomJS
from bokeh.models.widgets import TextInput, Select, RangeSlider, Slider, CheckboxGroup, Panel, Tabs, Button #, DataTable, TableColumn
from bokeh.plotting import figure

## Setup data and SQL

engine = sqlalchemy.create_engine('sqlite:///./test.db')
metadata = sqlalchemy.MetaData()
metadata.reflect(bind=engine)
dmo = metadata.tables['dmo']
disk = metadata.tables['disk']
conn = engine.connect()

df = pd.read_sql(sqlalchemy.select([dmo]).where(and_(dmo.c.vmax > 100, dmo.c.dist < 100)),conn)
df2 = pd.read_sql(sqlalchemy.select([disk]).where(and_(disk.c.vmax > 100, disk.c.dist < 100)),conn)
download_dmo_sub = ColumnDataSource(data=df)
download_dmo_all = ColumnDataSource(data=pd.read_sql(sqlalchemy.select([dmo]),conn))
download_disk_sub = ColumnDataSource(data=df2)
download_disk_all = ColumnDataSource(data=pd.read_sql(sqlalchemy.select([disk]),conn))
source = ColumnDataSource(data={'x' : df['vmax'], 'y' : df['mvir'], 'host_id' : df['host_id'].astype(str)})
source2 = ColumnDataSource(data={'x' : df2['vmax'], 'y' : df2['mvir'], 'host_id' : df2['host_id'].astype(str)})
plot_data = ColumnDataSource(data={'x' : [], 'y' : []})
plot_data2 = ColumnDataSource(data={'x' : [], 'y' : []})

## Build Bokeh inputs and callbacks

col_exclude = ['x', 'y', 'z', 'index', 'host_id']
col_allow = [i for i in df.columns if i not in col_exclude]

sql_query = TextInput(value="where vmax > 10 and dist < 100", title='SQL filter:')
sql_query2 = TextInput(value="where vmax > 10 and dist < 100", title='SQL filter:')
log_axes = CheckboxGroup(labels=["Log(x)", "Log(y)"], active=[], inline=True)
column1 = Select(title="X-axis Data:", value="vmax", options=col_allow)
column2 = Select(title="Y-axis Data:", value="mvir", options=col_allow)
plot_type = Select(title="Standard plots:", value="Infall", options=["Infall", "Mvir","Vmax", "Vpeak","Pericenter"]) # Add AM maybe?

labels_dict = dict(vmax='Vmax (km/s)', mvir='Mvir (M_sun)', rvir='Rvir (kpc)', 
                   dist='Dist from MW (kpc)', peri='Pericenter (kpc)', vpeak='Vpeak (km/s)',
                   vr='Radial Velocity (km/s)', vtan='Tangential Velocity (km/s)', infall='Infall Time (Gyrs)')

hover = HoverTool(tooltips=[('Host', '@host_id'),
                            ('{}'.format(column1.value), '@x'),
                            ('{}'.format(column2.value), '@y')])

id_list = df['host_id'].unique().astype(str).tolist()

color_mapper = CategoricalColorMapper(factors=id_list, palette=Category20[12])

button_dmo_sub = Button(label="Download DMO Query", button_type="primary")
button_dmo_all = Button(label="Download DMO Catalog", button_type="primary")
button_disk_sub = Button(label="Download Disk Query", button_type="danger")
button_disk_all = Button(label="Download Disk Catalog", button_type="danger")
button_dmo_sub.callback = CustomJS(args=dict(source=download_dmo_sub), 
                               code=open(join(dirname(__file__), "download.js")).read())
button_dmo_all.callback = CustomJS(args=dict(source=download_dmo_all), 
                               code=open(join(dirname(__file__), "download.js")).read())
button_disk_sub.callback = CustomJS(args=dict(source=download_disk_sub), 
                               code=open(join(dirname(__file__), "download.js")).read())
button_disk_all.callback = CustomJS(args=dict(source=download_disk_all), 
                               code=open(join(dirname(__file__), "download.js")).read())

p = figure(x_axis_label="Vmax (km/s)", y_axis_label="Mvir (M_sun)")
p.circle('x','y', source=source, 
         color='black',#dict(field='host_id', transform=color_mapper), 
         legend='DMO',#'host_id',
         size=7)
p.circle('x', 'y', source=source2,
         color='magenta',
         legend='Disk',
         size=7,
         fill_alpha=0.5)
p.add_tools(hover)
p.legend.location = 'top_left'
p.legend.click_policy = 'hide'
p.legend.background_fill_alpha = 0.5

def query_change(attr, old, new):
    '''
        This function takes the SQL query and alters it slightly to make
        the query apply to both the DMO and Disk tables
    '''
    s = 'select * from dmo ' + new
    s2 = 'select * from disk ' + new

    sql_query.value = new
    sql_query2.value = new

    global df, df2
    df = pd.read_sql(s,conn)
    df2 = pd.read_sql(s2,conn)
    column1.options = col_allow
    column2.options = col_allow
    column_change([], [], [])
    create_line_plot([],[],plot_type.value) 

def scale_axes(attr, old, new):
    '''
        Applies log-scaling using checkboxes.
    '''
    new_x = source.data['x']
    new_y = source.data['y']
    new_x2 = source2.data['x']
    new_y2 = source2.data['y']

    if (0 in new) and (0 not in old):
        new_x = np.log10(new_x)
        new_x2 = np.log10(new_x2)
        p.xaxis.axis_label = "Log10  " + labels_dict[column1.value]
    if (0 not in new) and (0 in old):
        new_x = df[column1.value]
        new_x2 = df2[column1.value]
        p.xaxis.axis_label = labels_dict[column1.value]
        
    if (1 in new) and (1 not in old):
        new_y = np.log10(new_y)
        new_y2 = np.log10(new_y2)
        p.yaxis.axis_label = "Log10  " + labels_dict[column2.value]
    if (1 not in new) and (1 in old):
        new_y = df[column2.value]
        new_y2 = df2[column2.value]
        p.yaxis.axis_label = labels_dict[column2.value]

    source.data = {'x' : new_x,
                   'y' : new_y, 
                   'host_id' : df['host_id'].astype(str)}

    source2.data = {'x' : new_x2,
                    'y' : new_y2, 
                    'host_id' : df2['host_id'].astype(str)}

def column_change(attr, old, new):
    '''
        Changes the values being plotted.
    '''
    new_x = df[column1.value]
    new_y = df[column2.value]
    new_x2 = df2[column1.value]
    new_y2 = df2[column2.value]

    if (0 in log_axes.active):
        p.xaxis.axis_label = "Log10  " + labels_dict[column1.value]
        new_x = np.log10(df[column1.value])
        new_x2 = np.log10(df2[column1.value])
    else:
        p.xaxis.axis_label = labels_dict[column1.value]

    if (1 in log_axes.active):
        p.yaxis.axis_label = "Log10  " + labels_dict[column2.value]
        new_y = np.log10(df[column2.value])
        new_y2 = np.log10(df2[column2.value])
    else:
        p.yaxis.axis_label = labels_dict[column2.value]

    hover.tooltips = [('Host', '@host_id'),
                      ('{}'.format(column1.value), '@x'),
                      ('{}'.format(column2.value), '@y')]

    source.data = {'x' : new_x, 
                   'y' : new_y, 
                   'host_id' : df['host_id'].astype(str)}

    source2.data = {'x' : new_x2,
                    'y' : new_y2, 
                    'host_id' : df2['host_id'].astype(str)}


def create_line_plot(attr, old, new):
    '''
        Generates what I consider the standard plots for this work.
    '''
    if new == "Infall":
        t = df['infall'].loc[df.infall < 13.8]
        hist, edges = np.histogram(t, bins=100, range=(0,13))
        hist = (np.sum(hist) - np.cumsum(hist))/np.sum(hist)
        plot_data.data = {'x' : edges[:-1],
                          'y' : hist}
        t = df2['infall'].loc[df2.infall < 13.8]
        hist, edges = np.histogram(t, bins=100, range=(0,13))
        hist = (np.sum(hist) - np.cumsum(hist))/np.sum(hist)
        plot_data2.data = {'x' : edges[:-1],
                          'y' : hist}
        p2.xaxis.axis_label = labels_dict['infall']
        p2.yaxis.axis_label = ""
    elif new == "Mvir":
        t = np.log10(df['mvir'].loc[df.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        plot_data.data = {'x' : edges[:-1],
                          'y' : hist}
        t = np.log10(df2['mvir'].loc[df2.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        plot_data2.data = {'x' : edges[:-1],
                          'y' : hist}
        p2.xaxis.axis_label = "Log10  " + labels_dict['mvir']
        p2.yaxis.axis_label = ""
    elif new == "Vmax":
        t = np.log10(df['vmax'].loc[df.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        plot_data.data = {'x' : edges[:-1],
                          'y' : hist}
        t = np.log10(df2['vmax'].loc[df2.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        plot_data2.data = {'x' : edges[:-1],
                          'y' : hist}
        p2.xaxis.axis_label = "Log10  " + labels_dict['vmax']
        p2.yaxis.axis_label = ""
    elif new == "Vpeak":
        t = np.log10(df['vpeak'].loc[df.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        plot_data.data = {'x' : edges[:-1],
                          'y' : hist}
        t = np.log10(df2['vpeak'].loc[df2.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.log10(np.sum(hist) - np.cumsum(hist))
        plot_data2.data = {'x' : edges[:-1],
                          'y' : hist}
        p2.xaxis.axis_label = "Log10  " + labels_dict['vpeak']
        p2.yaxis.axis_label = ""
    elif new == "Pericenter":
        t = (df['peri'].loc[df.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.cumsum(hist)/hist.sum()
        plot_data.data = {'x' : edges[:-1],
                          'y' : hist}
        t = (df2['peri'].loc[df2.dist > 0])
        hist, edges = np.histogram(t, bins=100)
        hist = np.cumsum(hist)/hist.sum()
        plot_data2.data = {'x' : edges[:-1],
                           'y' : hist}
        p2.xaxis.axis_label = labels_dict['peri']
        p2.yaxis.axis_label = ""

p2 = figure()
p2.line('x', 'y', source=plot_data, color='black', legend='DMO')
p2.line('x', 'y', source=plot_data2, color='magenta', legend='Disk')
p2.legend.click_policy = 'hide'
    
sql_query.on_change('value', query_change)
sql_query2.on_change('value', query_change)
log_axes.on_change('active', scale_axes)
column1.on_change('value', column_change)
column2.on_change('value', column_change)
plot_type.on_change('value', create_line_plot)

download_buttons = widgetbox([button_dmo_sub, button_dmo_all, button_disk_sub, button_disk_all], sizing_mode='scale_both')
tab1 = Panel(child=row(column(sql_query, log_axes, column1, column2, download_buttons),p), title='Explore')
tab2 = Panel(child=row(column(sql_query2, plot_type),p2), title='Relations')
tabs = Tabs(tabs=[tab1,tab2])

layout = row(sql_query, tabs)

create_line_plot([],[],'Infall')

curdoc().add_root(tabs)

# plots = column()
# data_table = DataTable(source=source,
#                        columns=[Table])

