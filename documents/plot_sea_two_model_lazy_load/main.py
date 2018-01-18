import os
import time
import sys
import urllib.request
import textwrap
import numpy
import iris

import bokeh.io
import bokeh.layouts 
import bokeh.models.widgets
import bokeh.plotting


import matplotlib
matplotlib.use('agg')

import lib_sea
import sea_plot
import sea_data

iris.FUTURE.netcdf_promote = True

try:
    get_ipython
    is_notbook = True
except:
    is_notebook = False


# Extract and Load
bucket_name = 'stephen-sea-public-london'
server_address = 'https://s3.eu-west-2.amazonaws.com'

fcast_time = '20180110T0000Z'

N1280_GA6_KEY = 'n1280_ga6'
KM4P4_RA1T_KEY = 'km4p4_ra1t'
KM1P5_INDO_RA1T_KEY = 'indon2km1p5_ra1t'
KM1P5_MAL_RA1T_KEY = 'mal2km1p5_ra1t'
KM1P5_PHI_RA1T_KEY = 'phi2km1p5_ra1t'

datasets = {N1280_GA6_KEY:{'model_name':'N1280 GA6 LAM Model'},
            KM4P4_RA1T_KEY:{'model_name':'SE Asia 4.4KM RA1-T '},
            KM1P5_INDO_RA1T_KEY:{'model_name':'Indonesia 1.5KM RA1-T'},
             KM1P5_MAL_RA1T_KEY:{'model_name':'Malaysia 1.5KM RA1-T'},
             KM1P5_PHI_RA1T_KEY:{'model_name':'Philipines 1.5KM RA1-T'},
           }
for ds_name in datasets.keys():
    datasets[ds_name]['var_lookup'] = sea_data.VAR_LOOKUP_RA1T

datasets[N1280_GA6_KEY]['var_lookup'] = sea_data.VAR_LOOKUP_GA6    

s3_base = '{server}/{bucket}/model_data/'.format(server=server_address,
                                                 bucket=bucket_name)
s3_local_base = os.path.join(os.sep,'s3',bucket_name, 'model_data')
base_path_local = os.path.expanduser('~/SEA_data/model_data/')
use_s3_mount = False
do_download = True


for ds_name in datasets.keys():
    fname1 = 'SEA_{conf}_{fct}.nc'.format(conf=ds_name, fct=fcast_time)
    datasets[ds_name]['data'] = sea_data.SEA_dataset(ds_name, 
                                                     fname1,
                                                     s3_base,
                                                     s3_local_base,
                                                     use_s3_mount,
                                                     base_path_local,
                                                     do_download,
                                                     datasets[ds_name]['var_lookup'],
                                                     )


#set up datasets dictionary

plot_names = ['precipitation',
              'air_temperature',
              'wind_vectors',
                'wind_mslp',
               'wind_streams',
               'mslp',
               'cloud_fraction',
               ]



# create regions
region_dict = {'indonesia': [-15.1, 1.0865, 99.875, 120.111],
               'malaysia': [-2.75, 10.7365, 95.25, 108.737],
               'phillipines': [3.1375, 21.349, 115.8, 131.987],
               'se_asia': [-18.0, 29.96, 90.0, 153.96],
              }

#Setup and display plots
plot_opts = lib_sea.create_colour_opts(plot_names)





init_time = 4
init_var = plot_names[0]
init_region = 'se_asia'
init_model_left = N1280_GA6_KEY # KM4P4_RA1T_KEY
init_model_right = KM4P4_RA1T_KEY # N1280_GA6_KEY


plot_obj_left = sea_plot.SEA_plot(datasets,
                         plot_opts,
                         'plot_sea_left',
                         init_var,
                         init_model_left,
                         init_region,
                         region_dict,
                        )

plot_obj_left.current_time = init_time
bokeh_img_left = plot_obj_left.create_plot()

plot_obj_right = sea_plot.SEA_plot(datasets,
                    plot_opts,
                    'plot_sea_right',
                    init_var,
                    init_model_right,
                    init_region,
                    region_dict,
                    )


plot_obj_right.current_time = init_time
bokeh_img_right = plot_obj_right.create_plot()

plots_row = bokeh.layouts.row(bokeh_img_left,
                              bokeh_img_right)

plot_obj_right.link_axes_to_other_plot(plot_obj_left)

# set up bokeh widgets
def create_dropdown_opt_list(iterable1):
    return [(k1,k1) for k1 in iterable1]

model_var_list_desc = 'Attribute to visualise'

model_var_dd = \
    bokeh.models.widgets.Dropdown(label=model_var_list_desc,
                                  menu=create_dropdown_opt_list(plot_names),
                                  button_type='warning')
model_var_dd.on_change('value',plot_obj_left.on_var_change)
model_var_dd.on_change('value',plot_obj_right.on_var_change)

num_times = datasets[N1280_GA6_KEY]['data'].get_data('precipitation').shape[0]
for ds_name in datasets:
    num_times = min(num_times, datasets[ds_name]['data'].get_data('precipitation').shape[0])
    
    
data_time_slider = bokeh.models.widgets.Slider(start=0, 
                                               end=num_times, 
                                               value=init_time, 
                                               step=1, 
                                               title="Data time")
                                               
data_time_slider.on_change('value',plot_obj_right.on_data_time_change)
data_time_slider.on_change('value',plot_obj_left.on_data_time_change)

region_desc = 'Region'

region_menu_list = create_dropdown_opt_list(region_dict.keys())
region_dd = bokeh.models.widgets.Dropdown(menu=region_menu_list, 
                                          label=region_desc,
                                          button_type='warning')
region_dd.on_change('value', plot_obj_right.on_region_change)
region_dd.on_change('value', plot_obj_left.on_region_change)

dataset_menu_list = create_dropdown_opt_list(datasets.keys())
left_model_desc = 'Left display'

left_model_dd = bokeh.models.widgets.Dropdown(menu=dataset_menu_list,
                                               label=left_model_desc,
                                               button_type='warning')
left_model_dd.on_change('value', plot_obj_left.on_config_change,)


right_model_desc = 'Right display'
right_model_dd = bokeh.models.widgets.Dropdown(menu=dataset_menu_list, 
                                             label=right_model_desc,
                                             button_type='warning')
right_model_dd.on_change('value', plot_obj_right.on_config_change)

# layout widgets
param_row = bokeh.layouts.row(model_var_dd, region_dd)
slider_row = bokeh.layouts.row(data_time_slider)
config_row = bokeh.layouts.row(left_model_dd, right_model_dd)

main_layout = bokeh.layouts.column(param_row, 
                                   slider_row,
                                   config_row,
                                   plots_row,
                                   )

try:
    bokeh_mode = os.environ['BOKEH_MODE']
except:
    bokeh_mode = 'server'    
    
if bokeh_mode == 'server':
    bokeh.plotting.curdoc().add_root(main_layout)
elif bokeh_mode == 'cli':
    bokeh.io.show(main_layout)
    
bokeh.plotting.curdoc().title = 'Lazy loading two model comparison'    
