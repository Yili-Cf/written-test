from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='集群名称')),
                ('code', models.CharField(max_length=64, unique=True, verbose_name='集群编码')),
                ('env', models.CharField(choices=[('dev', '开发'), ('test', '测试'), ('prod', '生产')], default='dev', max_length=16, verbose_name='环境')),
                ('description', models.TextField(blank=True, default='', verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '集群',
                'verbose_name_plural': '集群',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='部门名称')),
                ('code', models.CharField(max_length=64, unique=True, verbose_name='部门编码')),
                ('description', models.TextField(blank=True, default='', verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '部门',
                'verbose_name_plural': '部门',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='InstanceDailyStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stat_date', models.DateField(db_index=True, verbose_name='统计日期')),
                ('dimension', models.CharField(choices=[('department', '按部门'), ('cluster', '按集群')], max_length=16, verbose_name='统计维度')),
                ('instance_count', models.PositiveIntegerField(default=0, verbose_name='实例数量')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cluster', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='daily_stats', to='inventory.cluster', verbose_name='集群')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='daily_stats', to='inventory.department', verbose_name='部门')),
            ],
            options={
                'verbose_name': '实例每日统计',
                'verbose_name_plural': '实例每日统计',
                'ordering': ['-stat_date', 'dimension'],
            },
        ),
        migrations.CreateModel(
            name='DatabaseInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='实例名称')),
                ('host', models.CharField(max_length=255, verbose_name='主机')),
                ('port', models.PositiveIntegerField(default=3306, verbose_name='端口')),
                ('db_type', models.CharField(choices=[('mysql', 'MySQL'), ('postgresql', 'PostgreSQL'), ('redis', 'Redis'), ('mongodb', 'MongoDB'), ('other', '其他')], default='mysql', max_length=32, verbose_name='数据库类型')),
                ('status', models.CharField(choices=[('running', '运行中'), ('stopped', '已停止'), ('unknown', '未知')], default='unknown', max_length=16, verbose_name='状态')),
                ('username', models.CharField(blank=True, default='', max_length=128, verbose_name='管理账号')),
                ('password_encrypted', models.TextField(blank=True, default='', verbose_name='加密密码')),
                ('last_password_rotated_at', models.DateTimeField(blank=True, null=True, verbose_name='上次密码轮换时间')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instances', to='inventory.cluster', verbose_name='所属集群')),
            ],
            options={
                'verbose_name': '数据库实例',
                'verbose_name_plural': '数据库实例',
                'ordering': ['-id'],
            },
        ),
        migrations.AddField(
            model_name='cluster',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='clusters', to='inventory.department', verbose_name='所属部门'),
        ),
        migrations.AddConstraint(
            model_name='instancedailystat',
            constraint=models.UniqueConstraint(fields=('stat_date', 'dimension', 'department', 'cluster'), name='uniq_daily_stat_dimension'),
        ),
        migrations.AddIndex(
            model_name='databaseinstance',
            index=models.Index(fields=['host', 'port'], name='inventory_d_host_6958ec_idx'),
        ),
        migrations.AddIndex(
            model_name='databaseinstance',
            index=models.Index(fields=['status'], name='inventory_d_status_7a6e74_idx'),
        ),
    ]
