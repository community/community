#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "../lib/github"
require_relative "../lib/discussions"
require "active_support/core_ext/date_time"

# This script takes context from a received webhook and creates a new discussion in the correct discussion category

repo_id = "MDEwOlJlcG9zaXRvcnkzMDE1NzMzNDQ="
announcements_category_id = "DIC_kwDOEfmk4M4CQbR2"
incident_label_id = "LA_kwDOEfmk4M8AAAABpaZlTA"

date = Time.now.strftime("%Y-%m-%d")

# we need to take the provided input and generate a new post
title = "[#{date}] Incident Thread"

body = <<~BODY
## :exclamation: An incident has been declared:

**#{ENV['PUBLIC_TITLE']}**

_Subscribe to this Discussion for updates on this incident. Please upvote or emoji react instead of commenting +1 on the Discussion to avoid overwhelming the thread. Any account guidance specific to this incident will be shared in thread and on the [Incident Status Page](#{ENV['INCIDENT_URL']})._
BODY

# we need to create a new discussion in the correct category with the correct label
begin
  Discussion.create_incident_discussion(
    repo_id:,
    title:,
    body:,
    category_id: announcements_category_id,
    labels: [incident_label_id]
  )
rescue => ArgumentError
  puts "ERROR: One or more arguments missing. #{ArgumentError.message}"
end
