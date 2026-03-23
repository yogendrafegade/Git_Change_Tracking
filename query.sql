select first_name, last_name, salary, department_id, job_id from employees where job_id =
(select job_id from employee_id in (1,2,3,4,5));