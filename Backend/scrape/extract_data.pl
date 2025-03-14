#!/usr/bin/perl

use HTML::TreeBuilder;
use JSON;
use open qw(:std :utf8);

sub trim {
  my ($str) = @_;
  $str =~ s/^[\s\x{00a0}]+//ur =~ s/[\s\x{00a0}]+$//ur =~ s/[\s\x{00a0}]+/ /ugr;
}

my $t = HTML::TreeBuilder->new;

open my $fh, '<:utf8', $ARGV[0] or die "$!: $ARGV[0]";
my $data = do { $/ = undef; <$fh> };
$t->parse_content($data);


# find page title
#
my @headers = map { trim $_->as_text } $t->look_down("_tag" => qr/h[12]/);

# find canonical link
my %links = map {
  trim($_->attr('hreflang')) => trim($_->attr('href'))
} $t->look_down('_tag' => 'link', rel => 'alternate');

# find keywords
my @keywords = map {
  trim($_)
} map {
  split /,\s+/, $_->attr('content')
} $t->look_down(
  '_tag' => 'meta',
  name => 'keywords'
);


my @blocks;
my %seen_content;
for ($t->look_down('_tag' => 'p')) {
  my $content = trim $_->as_text;

  my @title_list = grep {
    defined
  } map {
    $_ ?  trim $_->as_text : undef
  } map {
    my $first_match = $_->look_down(class => qr/uk-accordion-title/)
  } grep {
    $_->attr('class') =~ qr/cp-accordion-item/;
  } $_->lineage;

  next unless $content && @title_list;

  push @blocks, {
    breadcrumbs => \@title_list,
    content => $content,
  };
  $seen_content{$content}++;
}


for ($t->look_down('_tag' => 'p')) {
  my $content = trim $_->as_text;
  next unless $content;
  push @blocks, {
    content => $content
  }
}

my $document = {
  headers => \@headers,
  links => \%links,
  blocks => \@blocks,
  keywords => \@keywords,
};

# use Data::Dumper;
# print Dumper($document);

print JSON::to_json($document, {utf8 => 0});
