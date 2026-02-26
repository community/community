#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussions"

# This script takes the context from the latest update dispatch event and updates the active incident discussion

# first, we must identify the correct incident to update, in the case where there are multiple open incident discussions.
discussion = Discussion.find_open_incident_discussions(owner: "community", repo: "community").keep_if { |d| d.body.include?("#{ENV["INCIDENT_SLUG"]}") }.first

if discussion.nil?
  puts "No applicable discussion, exiting"
  exit
end

# next, we need to update the discussion with the new information
update = "### Update \n #{ENV["INCIDENT_MESSAGE"]}"

discussion.add_comment(body: update)
