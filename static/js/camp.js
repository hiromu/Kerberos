function select(speed) {
    if ($('select#place').val() == -1)
        $('div.place').show(speed);
    else
        $('div.place').hide(speed);
}

select(0);
