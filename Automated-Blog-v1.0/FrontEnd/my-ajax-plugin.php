<?php
/*
Plugin Name: My AJAX Plugin
Plugin URI: https://example.com/my-ajax-plugin
Description: A plugin that demonstrates how to use AJAX in WordPress
Version: 1.0.0
Author: Daniel Lang
Author URI: https://example.com
*/

// Activation hook
register_activation_hook(__FILE__, 'my_ajax_plugin_activate');

function my_ajax_plugin_activate() {
    // Activation code if needed
}

// Enqueue scripts
function my_ajax_plugin_enqueue_scripts() {
    // Enqueue your JavaScript file
    wp_enqueue_script('my-ajax-script', plugins_url('js/my-script.js', __FILE__), array('jquery'), '1.0.0', true);

    // Localize the AJAX URL
    wp_localize_script('my-ajax-script', 'my_ajax_object', array(
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('my-ajax-nonce')
    ));
}
add_action('wp_enqueue_scripts', 'my_ajax_plugin_enqueue_scripts');

// AJAX handler
add_action('wp_ajax_my_ajax_action', 'my_ajax_handler');
add_action('wp_ajax_nopriv_my_ajax_action', 'my_ajax_handler');

function my_ajax_handler() {
    // Verify the AJAX nonce
    check_ajax_referer('my-ajax-nonce', 'nonce');

    // Process the AJAX request
    // Example: Send an email or perform other actions
    wp_send_json_success('AJAX request successful!');
}
