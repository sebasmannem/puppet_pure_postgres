# == Class: pure_postgres
#
# Module for doing postgres stuff with pure distribution.
class pure_postgres
(
  $repo              = $pure_postgres::params::repo,
  $version           = $pure_postgres::params::version,
  $package_name      = $pure_postgres::params::package_name,
  $package_version   = $pure_postgres::params::package_version
) inherits pure_postgres::params
{
   class { 'pure_postgres::repo':
      repo              => $repo,
      version           => $version,
      package_name      => $package_name,
      package_version   => $package_version
   }
   class { 'pure_postgres::postgresql':
      pg_version        => $pure_postgres::params::pg_version
   }

}
