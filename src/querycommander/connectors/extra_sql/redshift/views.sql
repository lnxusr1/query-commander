select viewname 
from pg_catalog.pg_views
    left join pg_catalog.stv_mv_info 
        on pg_views.schemaname = stv_mv_info.schema and pg_views.viewname = stv_mv_info.name and coalesce(stv_mv_info.db_name,'-1') in (%s,'-1')
where stv_mv_info.name is null and schemaname = %s order by viewname