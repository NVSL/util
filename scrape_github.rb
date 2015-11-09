#!/usr/bin/env ruby

require 'mechanize'

agent = Mechanize.new
agent.user_agent_alias = 'Mac Safari'

`mkdir -p brds/tmp`
`mkdir brds/keep`

page = agent.get('https://github.com/search?l=eagle&q=net+name+extension%3Asch&ref=searchresults&type=Code&utf8=%E2%9C%93')
100.times do |i|
    page.links_with(:href => /\.sch$/).each do |link|
        sleep(rand*1.5)
        url = 'https://raw.githubusercontent.com' + link.href.gsub("blob/","")
        puts url.chars.last(30).join
        `wget -q -nc -P brds/tmp "#{url}"`
        name = `ls brds/tmp/`.strip
        # n=`countparts.py "brds/tmp/#{name}"`.to_i
        n = 16
        print n
        if n >= 15
            puts " -- keeper"
            `cp brds/tmp/* brds/keep/`
        else
            puts " -- too easy"
        end
        `rm -f brds/tmp/*`
    end
    link = page.link_with(:href => /search/, :class => /next_page/)
    puts link.href
    page = agent.click(link)
end



