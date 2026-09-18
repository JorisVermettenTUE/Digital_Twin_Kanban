update public.tasks
set status = 'In review'
where status = 'Geblokkeerd';

alter table public.tasks
drop constraint if exists tasks_status_check;

alter table public.tasks
add constraint tasks_status_check
check (
    status in (
        'Niet gestart',
        'In uitvoering',
        'In review',
        'Klaar'
    )
);
