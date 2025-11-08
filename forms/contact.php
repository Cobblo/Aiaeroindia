<?php
// Database connection details
$host = "localhost"; // Change if your database is hosted elsewhere
$dbname = "contact_form_db";
$username = "root"; // Change as per your database username
$password = ""; // Change as per your database password

// Create a connection
$conn = new mysqli($host, $username, $password, $dbname);

// Check the connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Check if form is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name = $conn->real_escape_string($_POST['name']);
    $email = $conn->real_escape_string($_POST['email']);
    $subject = $conn->real_escape_string($_POST['subject']);
    $message = $conn->real_escape_string($_POST['message']);

    // Insert data into database
    $sql = "INSERT INTO contacts (name, email, subject, message) 
            VALUES ('$name', '$email', '$subject', '$message')";

    if ($conn->query($sql) === TRUE) {
        // If data is saved, send the email
        $to = "your-email@example.com"; // Change to your actual email
        $headers = "From: $email" . "\r\n" . "Reply-To: $email";

        if (mail($to, $subject, $message, $headers)) {
            echo "Message sent and saved successfully!";
        } else {
            echo "Message saved, but email failed to send.";
        }
    } else {
        echo "Error: " . $sql . "<br>" . $conn->error;
    }
}

// Close the database connection
$conn->close();
?>
