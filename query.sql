select first_name as fname, last_name as lname, salary, department_id, job_id from employees e where job_id in (select
job_id from departments) order by 1 asc, 3 desc;