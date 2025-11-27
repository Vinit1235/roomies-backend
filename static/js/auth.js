document.addEventListener('DOMContentLoaded', function() {
    // Toggle college field visibility based on role selection
    const studentRadio = document.getElementById('student');
    const ownerRadio = document.getElementById('owner');
    const collegeField = document.getElementById('collegeField');
    const collegeSelect = document.getElementById('collegeSelect');
    
    function toggleCollegeField() {
        if (studentRadio && studentRadio.checked) {
            // Show college field for students
            collegeField.style.display = 'block';
            collegeSelect.required = true;
        } else if (ownerRadio && ownerRadio.checked) {
            // Hide college field for owners
            collegeField.style.display = 'none';
            collegeSelect.required = false;
            collegeSelect.value = ''; // Clear selection
        }
    }
    
    // Add event listeners to role radio buttons
    if (studentRadio) {
        studentRadio.addEventListener('change', toggleCollegeField);
    }
    if (ownerRadio) {
        ownerRadio.addEventListener('change', toggleCollegeField);
    }
    
    // Initialize on page load
    toggleCollegeField();
});
