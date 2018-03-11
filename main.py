import pandas as pd
import sqlalchemy
import numpy as np

from bokeh.io import curdoc
from bokeh.palettes import Category20
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, CategoricalColorMapper
from bokeh.models.widgets import TextInput, Select, RangeSlider, Slider, CheckboxGroup #, DataTable, TableColumn, Panel, Tabs
from bokeh.plotting import figure

## Setup data and SQL

engine = sqlalchemy.create_engine('sqlite:///test.db')
metadata = sqlalchemy.MetaData()
metadata.reflect(bind=engine)
dmo = metadata.tables['dmo']
disk = metadata.tables['disk']
conn = engine.connect()

df = pd.read_sql(sqlalchemy.select([dmo]).where(dmo.c.vmax > 100),conn)
source = ColumnDataSource(data={'x' : df['vmax'], 'y' : df['mvir'], 'host_id' : df['host_id'].astype(str)})

## Build Bokeh inputs and callbacks

col_exclude = ['x', 'y', 'z', 'index', 'host_id']

sql_query = TextInput(value="", title='SQL Query:')
log_axes = CheckboxGroup(labels=["Log(x)", "Log(y)"], active=[])
column1 = Select(title="X-axis Data:", value="vmax", options=[i for i in df.columns if i not in col_exclude])
column2 = Select(title="Y-axis Data:", value="mvir", options=[i for i in df.columns if i not in col_exclude])

labels_dict = dict(vmax='Vmax (km/s)', mvir='Mvir (M_sun)', rvir='Rvir (kpc)', 
				   dist='Dist from MW (kpc)', peri='Pericenter (kpc)', vpeak='Vpeak (km/s)',
				   vr='Radial Velocity (km/s)', vtan='Tangential Velocity (km/s)', infall='Infall Time (Gyrs)')

hover = HoverTool(tooltips=[('Host', '@host_id'),
							('{}'.format(column1.value), '@x'),
							('{}'.format(column2.value), '@y')])

id_list = df['host_id'].unique().astype(str).tolist()

color_mapper = CategoricalColorMapper(factors=id_list, palette=Category20[12])

p = figure(x_axis_label="Vmax (km/s)", y_axis_label="Mvir (M_sun)")
p.circle('x','y', source=source, 
		 color=dict(field='host_id', transform=color_mapper), 
		 legend='host_id',
		 size=7)
p.add_tools(hover)

p.legend.location = 'top_left'
p.legend.background_fill_alpha = 0.5

def query_change(attr, old, new):
	s = sql_query.value
	if ('host_id' not in s.split('select ')[-1].split(' from')[0]) and ('*' not in s):
		s = 'select ' + 'host_id,' + s.split('select ')[-1]

	global df
	df = pd.read_sql(s,conn)
	column1.options = [i for i in df.columns if i not in col_exclude]
	column2.options = [i for i in df.columns if i not in col_exclude]
	column_change([], [], []) 

def scale_axes(attr, old, new):
	new_x = source.data['x']
	new_y = source.data['y']

	if (0 in new) and (0 not in old):
		new_x = np.log10(new_x)
		p.xaxis.axis_label = "Log10  " + labels_dict[column1.value]
	if (0 not in new) and (0 in old):
		new_x = df[column1.value]
		p.xaxis.axis_label = labels_dict[column1.value]
		
	if (1 in new) and (1 not in old):
		new_y = np.log10(new_y)
		p.yaxis.axis_label = "Log10  " + labels_dict[column2.value]
	if (1 not in new) and (1 in old):
		new_y = df[column2.value]
		p.yaxis.axis_label = labels_dict[column2.value]

	source.data = {'x' : new_x,
				   'y' : new_y, 
				   'host_id' : df['host_id'].astype(str)}

def column_change(attr, old, new):
	new_x = df[column1.value]
	new_y = df[column2.value]

	if (0 in log_axes.active):
		p.xaxis.axis_label = "Log10  " + labels_dict[column1.value]
		new_x = np.log10(df[column1.value])
	else:
		p.xaxis.axis_label = labels_dict[column1.value]

	if (1 in log_axes.active):
		p.yaxis.axis_label = "Log10  " + labels_dict[column2.value]
		new_y = np.log10(df[column2.value])
	else:
		p.yaxis.axis_label = labels_dict[column2.value]

	hover.tooltips = [('Host', '@host_id'),
					  ('{}'.format(column1.value), '@x'),
					  ('{}'.format(column2.value), '@y')]

	source.data = {'x' : new_x, 
				   'y' : new_y, 
				   'host_id' : df['host_id'].astype(str)}
    
sql_query.on_change('value', query_change)
log_axes.on_change('active', scale_axes)
column1.on_change('value', column_change)
column2.on_change('value', column_change)

layout = row(column(sql_query, log_axes, column1, column2), p)

curdoc().add_root(layout)

# plots = column()
# data_table = DataTable(source=source,
#                        columns=[Table])
# tab1 = Panel(child=plots, title='Figures')
# tab2 = Panel(child=data_table, title='Table')
# tabs = Tabs(tabs=[tab1,tab2])