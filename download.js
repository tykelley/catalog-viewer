var data = source.data;
var filetext =  'index,host_id,id,mass,rs,rvir,vmax,vx,vy,vz,x,y,z,vpeak,scale_vpeak,dist,infall,peri\n';
for (var i = 0; i < data['index'].length; i++) {
    var currRow = [data['index'][i].toString(),
                   data['host_id'][i].toString(),
                   data['id'][i].toString(),
                   data['mass'][i].toString(),
                   data['rs'][i].toString(),
                   data['rvir'][i].toString(),
                   data['vmax'][i].toString(),
                   data['vx'][i].toString(),
                   data['vy'][i].toString(),
                   data['vz'][i].toString(),
                   data['x'][i].toString(),
                   data['y'][i].toString(),
                   data['z'][i].toString(),
                   data['vpeak'][i].toString(),
                   data['scale_vpeak'][i].toString(),
                   data['dist'][i].toString(),
                   data['infall'][i].toString(),
                   data['peri'][i].toString().concat('\n')];

    var joined = currRow.join();
    filetext = filetext.concat(joined);
}

var filename = fname;
var blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });

//addresses IE
if (navigator.msSaveBlob) {
    navigator.msSaveBlob(blob, filename);
} else {
    var link = document.createElement("a");
    link = document.createElement('a')
    link.href = URL.createObjectURL(blob);
    link.download = filename
    link.target = "_blank";
    link.style.visibility = 'hidden';
    link.dispatchEvent(new MouseEvent('click'))
}