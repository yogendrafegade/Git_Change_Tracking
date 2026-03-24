SELECT 
    e.first_name AS fname,
    e.last_name AS lname,
    e.salary,
    e.department_id,
    e.job_id,
    l.location_id,
    l.city,
    l.state_province,
    l.country_id
FROM employees e
JOIN departments d 
    ON e.department_id = d.department_id
JOIN locations l 
    ON d.location_id = l.location_id
WHERE e.job_id IN (
    SELECT job_id 
    FROM departments
)
ORDER BY fname ASC, salary DESC;